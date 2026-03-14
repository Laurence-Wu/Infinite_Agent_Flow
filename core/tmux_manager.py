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

Startup / "yolo" consent flow
------------------------------
After launching the agent command the startup thread does NOT blindly send
Ctrl+Y.  Instead it:

  1. Waits up to 30 s for *any* pane output.
  2. Reads the pane and calls probe_pane_state() to classify the current state.
  3. Only when the state is CONSENT_PENDING does it send Ctrl+Y ("yolo event").
  4. If the state is QUOTA_EXCEEDED or NEEDS_INTERVENTION the thread logs and
     aborts without sending anything — the caller will see those states via
     probe_state() / status().
  5. After accepting consent it waits for the prompt (PromptDetector) and then
     pastes AGENT_LOOP.md.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from pathlib import Path
from typing import Generator

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
        lines = self.capture(30)
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
        self._run("send-keys", "-t", self._session, self._agent_command, "Enter")
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
            self._interrupt(count=2)
        else:
            ws = self._wsl_path(self._workspace)
            self._run("new-session", "-d", "-s", self._session, "-c", ws)

        self._run("send-keys", "-t", self._session, self._agent_command, "Enter")
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

    def _send_yolo_consent(self) -> bool:
        """
        Verify the pane currently shows the consent/ToS screen, then send Ctrl+Y.

        Returns True when Ctrl+Y was sent, False when the pane state did not
        confirm CONSENT_PENDING (nothing is sent in that case).
        """
        lines = self.capture(30)
        state = probe_pane_state(lines)

        if state == AgentState.CONSENT_PENDING:
            self._run("send-keys", "-t", self._session, "C-y", "")
            logger.info(
                "tmux session '%s': consent screen confirmed → sent Ctrl+Y (yolo event)",
                self._session,
            )
            return True

        if state == AgentState.QUOTA_EXCEEDED:
            logger.error(
                "tmux session '%s': quota exceeded — cannot start agent. "
                "Check your Gemini API quota.",
                self._session,
            )
        elif state == AgentState.NEEDS_INTERVENTION:
            logger.error(
                "tmux session '%s': agent needs intervention (auth error or fatal). "
                "Pane content:\n%s",
                self._session, "\n".join(lines[-10:]),
            )
        else:
            logger.warning(
                "tmux session '%s': expected CONSENT_PENDING but got %s — "
                "skipping Ctrl+Y. Pane content:\n%s",
                self._session, state.value, "\n".join(lines[-10:]),
            )
        return False

    def _startup_sequence(self) -> None:
        """
        Background thread: detect consent screen → send Ctrl+Y only when
        confirmed → wait for prompt → paste loop file.

        Sets self._starting = False when done (or on failure).
        """
        try:
            # 1. Wait until gemini has printed anything at all
            if not self._wait_for_any_output(timeout=30):
                logger.warning(
                    "tmux session '%s': no output after 30 s — aborting startup",
                    self._session,
                )
                return

            # 2. Check pane state and send Ctrl+Y *only* when consent screen visible
            consent_sent = self._send_yolo_consent()

            # 3. If agent is in a broken state, abort now
            if not consent_sent:
                state = probe_pane_state(self.capture(30))
                if state in (AgentState.QUOTA_EXCEEDED, AgentState.NEEDS_INTERVENTION):
                    self._agent_state = state
                    return
                # Otherwise (STARTING / RUNNING / etc.) — let it proceed; maybe
                # it didn't show a consent screen on this run (already accepted).

            # 4. Wait for the agent to be fully ready
            self._detector.wait(session_name=self._session)

            if not self.is_alive():
                logger.warning("tmux session '%s' died during startup", self._session)
                return

            # 5. Paste the loop file
            self._paste_loop_file()

            # 6. Final probe so status() is accurate immediately after startup
            self._agent_state = probe_pane_state(self.capture(30))

        finally:
            self._starting = False

    def _paste_loop_file(self) -> None:
        """Load AGENT_LOOP.md into the tmux buffer and paste it into the pane."""
        loop_path = self._wsl_path(self._loop_file)
        self._run("load-buffer", loop_path)
        self._run("paste-buffer", "-t", self._session)
        self._run("send-keys", "-t", self._session, "", "Enter")
        logger.info("AGENT_LOOP.md pasted into tmux session '%s'", self._session)
