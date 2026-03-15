"""
TmuxManager — high-level session lifecycle for the AI agent.

Composes TmuxBase (low-level tmux commands) and PromptDetector (readiness
detection) to implement the agent session state machine:

    DEAD ──start()──► STARTING ──prompt detected──► RUNNING
                                                        │
                                               pause() ─┤─ stop()
                                                        │       │
                                                     PAUSED   DEAD
                                                        │
                                               restart()─┴──► STARTING ──► RUNNING

Controls
--------
start()        — create session (if needed), launch agent, wait for prompt, paste loop file
stop()         — send Ctrl+C × 2, kill session
pause()        — send Esc (interrupts mid-generation without killing)
restart()      — send Ctrl+C × 2 (keep session alive), relaunch agent, wait, paste loop file
probe_state()  — inspect live pane and return AgentState without side-effects

Startup / "yolo" flow  (start and restart share the same _startup_sequence)
------------------------------------------------------------------------------
  1. Wait up to 30 s for *any* pane output.
  2. Classify pane state (probe_pane_state):
       - QUOTA_EXCEEDED / NEEDS_INTERVENTION → abort immediately.
       - CONSENT_PENDING → send Ctrl+Y (accept ToS), sleep 1 s, continue.
       - Anything else   → no early action.
  3. AgentProfile.wait_for_box()  ← GATE before first interaction.
  4. [separate] Send Ctrl+Y        → yolo mode (auto-accept tool calls).
  5. sleep 0.5 s.
  6. AgentProfile.wait_for_box()  ← gate before paste.
  7. [separate] load-buffer        → load AGENT_LOOP.md into tmux buffer.
  8. sleep 0.5 s.
  9. [separate] paste-buffer       → paste into the input box.
 10. sleep 0.5 s.
 11. AgentProfile.wait_for_box()  ← gate before Enter.
 12. [separate] send-keys Enter    → submit.

AgentProfile (core/agent_profile.py) defines what "UI box visible" means for
each agent.  The default Gemini profile checks for "Type your message" / "> "
/ "❯ " in the last 5 pane lines.  Override by editing agents/gemini.json.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from pathlib import Path
from typing import Generator

from core.agent_profile import AgentProfile
from core.tmux_base     import TmuxBase
from core.tmux_detector import AgentState, PromptDetector, probe_pane_state

logger = logging.getLogger(__name__)


class TmuxManager(TmuxBase):
    """Controls a single named tmux session for the workspace AI agent."""

    def __init__(
        self,
        workspace:     Path,
        session_name:  str,
        loop_file:     Path,
        agent_command: str = "gemini",
        startup_wait:  int = 120,
    ) -> None:
        super().__init__(workspace, session_name)
        self._loop_file      = Path(loop_file).resolve()
        self._agent_command  = agent_command
        self._startup_wait   = startup_wait
        self._starting       = False  # True while background startup thread is running
        self._agent_state    = AgentState.DEAD  # last known probed state
        self._detector       = PromptDetector(
            capture_fn  = self.capture,
            is_alive_fn = self.is_alive,
            timeout     = startup_wait,
        )
        agents_dir      = Path(__file__).resolve().parent.parent / "agents"
        self._profile   = AgentProfile.for_command(agent_command, agents_dir=agents_dir)
        # Live pane streaming state
        self._pane_buffer: deque[str]         = deque(maxlen=500)
        self._pane_lock                        = threading.Lock()
        self._pane_event                       = threading.Event()
        self._last_snap: str                   = ""
        self._capture_thread: threading.Thread | None = None

    # ------------------------------------------------------------------ #
    #  Public properties
    # ------------------------------------------------------------------ #

    @property
    def agent_command(self) -> str:
        """The CLI command used to launch the AI agent."""
        return self._agent_command

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def probe_state(self) -> AgentState:
        """
        Read the live pane (non-blocking) and return the current AgentState.

        Returns AgentState.DEAD when the session does not exist.
        Call this before any command to know whether the agent can accept input.
        """
        if not self.is_alive():
            self._agent_state = AgentState.DEAD
            return AgentState.DEAD
        # visible_only=True: probe only the live screen, not stale scrollback
        lines = self.capture(30, visible_only=True)
        state = probe_pane_state(lines)
        self._agent_state = state
        return state

    def start(self) -> None:
        """
        Create the tmux session (if not already alive), launch the agent,
        then in a background thread: detect consent screen → send Ctrl+Y only
        when confirmed → wait for the prompt → paste AGENT_LOOP.md.

        Returns immediately — check status()['starting'] for progress.
        """
        if self.is_alive():
            logger.info("tmux session '%s' already running — skipping start", self._session)
            self._ensure_capture_thread()
            return

        ws = self._wsl_path(self._workspace)
        self._run("new-session", "-d", "-s", self._session, "-c", ws)
        self._run("send-keys", "-t", self._session, self._agent_command, "")
        self._run("send-keys", "-t", self._session, "", "Enter")
        logger.info(
            "tmux session '%s' created — running '%s'",
            self._session, self._agent_command,
        )

        self._starting = True
        threading.Thread(
            target=self._startup_sequence,
            daemon=True,
            name="tmux-start",
        ).start()
        self._ensure_capture_thread()

    def stop(self) -> None:
        """Send Ctrl+C × 2 then kill the session."""
        if not self.is_alive():
            return
        self._interrupt(count=2)
        self._run("kill-session", "-t", self._session)
        self._agent_state = AgentState.DEAD
        logger.info("tmux session '%s' stopped", self._session)

    def pause(self) -> None:
        """Send Esc to interrupt mid-generation without killing the session."""
        if not self.is_alive():
            return
        self._run("send-keys", "-t", self._session, "Escape", "")
        logger.info("Sent Esc to tmux session '%s' (paused)", self._session)

    def restart(self) -> None:
        """
        Interrupt the current agent (Ctrl+C × 2) without killing the session,
        then relaunch the agent command and wait for it to be ready before
        re-pasting AGENT_LOOP.md.

        If the session is dead, creates a fresh one first.
        """
        if self.is_alive():
            # Escape first: cancel any mid-generation output without submitting
            self._run("send-keys", "-t", self._session, "Escape", "")
            time.sleep(0.3)
            self._interrupt(count=3)
            # Verify we're back at the shell — TUI decorators (────) disappear
            # once the agent process exits. Keep sending Ctrl+C until they're gone
            # or we time out (5 s).
            deadline = time.time() + 5
            while time.time() < deadline:
                lines = self.capture(5, visible_only=True)
                joined = "\n".join(lines)
                if "─" not in joined and "│" not in joined:
                    break  # no TUI box-drawing chars — back at shell
                self._run("send-keys", "-t", self._session, "C-c", "")
                time.sleep(0.5)
        else:
            ws = self._wsl_path(self._workspace)
            self._run("new-session", "-d", "-s", self._session, "-c", ws)

        # Clear visible screen + scrollback so _startup_sequence starts from a
        # blank pane. Without this, the old TUI content remains visible and
        # wait_for_box() fires immediately on stale "Type your message" tokens
        # before the new agent has rendered anything.
        self._run("send-keys", "-t", self._session, "clear", "")
        self._run("send-keys", "-t", self._session, "", "Enter")
        self._run("clear-history", "-t", self._session)
        time.sleep(0.3)  # let clear execute and shell settle

        self._run("send-keys", "-t", self._session, self._agent_command, "")
        self._run("send-keys", "-t", self._session, "", "Enter")
        logger.info("Restart: launched '%s' in session '%s'", self._agent_command, self._session)

        self._starting = True
        threading.Thread(
            target=self._startup_sequence,
            daemon=True,
            name="tmux-restart",
        ).start()
        self._ensure_capture_thread()

    def status(self) -> dict:
        """Return a status dict suitable for the /api/agent endpoint."""
        alive = self.is_alive()
        return {
            "alive":         alive,
            "starting":      self._starting,
            "agent_state":   self._agent_state.value,
            "session_name":  self._session,
            "agent_command": self._agent_command,
            "workspace":     str(self._workspace),
            "pane_lines":    self.capture(30) if alive else [],
        }

    def stream_lines(self, timeout: float = 30.0) -> Generator[str, None, None]:
        """
        Generator: yield buffered pane lines immediately, then block and yield
        new lines as they arrive. Intended for SSE use — each client gets its
        own cursor into the shared ring buffer.
        """
        # Snapshot the current buffer so new clients see recent history
        with self._pane_lock:
            initial = list(self._pane_buffer)
        cursor = len(initial)
        yield from initial

        while True:
            fired = self._pane_event.wait(timeout=timeout)
            if not fired:
                # Timeout — yield a keep-alive comment so the connection stays open
                yield ": keep-alive"
                continue
            self._pane_event.clear()
            with self._pane_lock:
                chunk = list(self._pane_buffer)[cursor:]
                cursor += len(chunk)
            yield from chunk

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _ensure_capture_thread(self) -> None:
        """Start the background pane-capture thread if it is not already running."""
        if self._capture_thread and self._capture_thread.is_alive():
            return
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="pane-capture",
        )
        self._capture_thread.start()
        logger.debug("pane-capture thread started for session '%s'", self._session)

    def _capture_loop(self) -> None:
        """Background thread: poll tmux pane every 1 s and push new lines to the buffer."""
        while True:
            time.sleep(1)
            if not self.is_alive():
                continue
            lines = self.capture(200)
            snap  = "\n".join(lines)
            if snap == self._last_snap:
                continue
            # Detect new suffix lines since last snapshot
            old_lines = self._last_snap.splitlines() if self._last_snap else []
            new_lines = lines[len(old_lines):] if len(lines) > len(old_lines) else lines
            self._last_snap = snap
            if new_lines:
                with self._pane_lock:
                    self._pane_buffer.extend(new_lines)
                self._pane_event.set()

    def _interrupt(self, count: int = 2) -> None:
        """Send Ctrl+C `count` times with a short pause between each."""
        for _ in range(count):
            self._run("send-keys", "-t", self._session, "C-c", "")
            time.sleep(0.3)
        time.sleep(0.5)

    def _wait_for_any_output(self, timeout: float = 30.0) -> bool:
        """Block until the pane has any non-empty content."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.capture(5):
                return True
            time.sleep(0.5)
        return False

    def _startup_sequence(self) -> None:
        """
        Background thread startup sequence:

          1. Wait for any pane output (gemini booting).
          2. Check for blocking states early (quota / intervention → abort).
             If consent screen is visible → send Ctrl+Y to accept ToS.
          3. AgentProfile.wait_for_box()  ← gate before Ctrl+Y.
          4. Send Ctrl+Y  (yolo mode — auto-accept tool calls).  [separate call]
          5. Sleep 0.5 s.
          6. Load AGENT_LOOP.md into the tmux buffer.            [local op]
          7. Sleep 0.5 s.
          8. AgentProfile.wait_for_box()  ← gate before paste.
          9. Paste buffer (bracketed -p) into input box.         [separate call]
         10. Sleep 0.5 s.
         11. AgentProfile.wait_for_box()  ← gate before Enter.
         12. Send Enter to submit.                               [separate call]
         13. Final state probe so status() is accurate immediately.

        Sets self._starting = False when done (or on failure).
        """
        try:
            # ── 1. Wait until gemini has printed anything ─────────────────
            if not self._wait_for_any_output(timeout=30):
                logger.warning(
                    "tmux session '%s': no output after 30 s — aborting startup",
                    self._session,
                )
                return

            # ── 2. Early blocking-state check ─────────────────────────────
            # visible_only=True: skip scrollback so stale bash errors from a
            # previous crashed session (e.g. "command not found" from a leaked
            # terminal escape sequence) don't false-trigger NEEDS_INTERVENTION.
            lines = self.capture(30, visible_only=True)
            state = probe_pane_state(lines)

            if state == AgentState.QUOTA_EXCEEDED:
                logger.error(
                    "tmux session '%s': quota exceeded — cannot start agent.",
                    self._session,
                )
                self._agent_state = AgentState.QUOTA_EXCEEDED
                return

            if state == AgentState.NEEDS_INTERVENTION:
                logger.error(
                    "tmux session '%s': agent needs intervention. Pane:\n%s",
                    self._session, "\n".join(lines[-10:]),
                )
                self._agent_state = AgentState.NEEDS_INTERVENTION
                return

            if state == AgentState.CONSENT_PENDING:
                # ToS screen appears before the TUI — accept it, then fall
                # through to wait for the UI box to become stable.
                self._run("send-keys", "-t", self._session, "C-y", "")
                logger.info(
                    "tmux session '%s': ToS consent screen → sent Ctrl+Y (accept)",
                    self._session,
                )
                time.sleep(1)   # let the consent animation settle

            # ── 3. Wait for UI input box — gate before Ctrl+Y ────────────
            # visible_only lambda: box detection must not read stale scrollback.
            if not self._profile.wait_for_box(
                lambda n: self.capture(n, visible_only=True), self.is_alive, self._session
            ):
                logger.warning(
                    "tmux session '%s': UI box not detected before Ctrl+Y — aborting",
                    self._session,
                )
                return

            # ── 4. Yolo mode — key sequence from agent profile ────────────
            # Gemini: ["C-y"]  |  Qwen: ["BTab", "BTab"] (Shift+Tab twice)
            for key in self._profile.yolo_keys:
                self._run("send-keys", "-t", self._session, key, "")
                time.sleep(0.1)
            logger.info(
                "tmux session '%s': UI box visible → sent yolo keys %s",
                self._session, list(self._profile.yolo_keys),
            )
            time.sleep(0.5)

            # ── 5. Load AGENT_LOOP.md into the tmux paste buffer ─────────
            loop_path = self._wsl_path(self._loop_file)
            self._run("load-buffer", loop_path)
            logger.info("tmux session '%s': loop file loaded into buffer", self._session)
            time.sleep(0.5)

            # ── 6. Wait for UI input box — gate before paste ──────────────
            if not self._profile.wait_for_box(
                lambda n: self.capture(n, visible_only=True), self.is_alive, self._session
            ):
                logger.warning(
                    "tmux session '%s': UI box not detected before paste — aborting",
                    self._session,
                )
                return

            # ── 7. Paste buffer (bracketed) into the input box ────────────
            # -p flag wraps content in \033[200~...\033[201~ so the TUI treats
            # the entire file as a single paste event — newlines are preserved
            # instead of being interpreted as Enter keypresses.
            self._run("paste-buffer", "-p", "-t", self._session)
            logger.info("tmux session '%s': buffer pasted into pane", self._session)
            time.sleep(0.5)

            # ── 8. Wait for UI input box — gate before Enter ──────────────
            if not self._profile.wait_for_box(
                lambda n: self.capture(n, visible_only=True), self.is_alive, self._session
            ):
                logger.warning(
                    "tmux session '%s': UI box not detected before Enter — aborting",
                    self._session,
                )
                return

            # ── 9. Press Enter to submit ──────────────────────────────────
            self._run("send-keys", "-t", self._session, "", "Enter")
            logger.info("tmux session '%s': Enter sent — AGENT_LOOP.md submitted", self._session)

            # ── 8. Final probe ────────────────────────────────────────────
            self._agent_state = probe_pane_state(self.capture(30))

        finally:
            self._starting = False

