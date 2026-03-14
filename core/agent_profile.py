"""
AgentProfile — per-agent UI input-box detection configuration.

Each AI agent CLI (Gemini, Claude, …) renders its input box differently.
AgentProfile encapsulates the tokens that signal "the input box is visible
and ready to receive keystrokes" so TmuxManager can gate every send-keys
call on confirmed box visibility.

Resolution order for a given agent command:
  1. agents/<name>.json  in the project root  (user-editable, no code change needed)
  2. Built-in _BUILTIN_PROFILES table
  3. _default fallback  (generic "> " / "❯ " prompt tokens)

Usage (TmuxManager.__init__)::

    from core.agent_profile import AgentProfile
    agents_dir = Path(__file__).resolve().parent.parent / "agents"
    self._profile = AgentProfile.for_command(self._agent_command, agents_dir=agents_dir)

Usage (startup sequence)::

    if not self._profile.wait_for_box(self.capture, self.is_alive, self._session):
        logger.warning("UI box not detected — proceeding anyway")
    self._run("send-keys", ...)
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentProfile:
    """
    Describes how to detect the input-ready state for a specific AI agent CLI.

    Parameters
    ----------
    name :
        Human-readable identifier (e.g. ``"gemini"``).
    ui_box_tokens :
        Strings that appear in the last few visible pane lines when the CLI
        input box is rendered and ready.  At least one must be present.
    box_wait_timeout :
        Maximum seconds to wait for the input box before giving up (the
        caller proceeds anyway after the timeout).
    box_poll_interval :
        Seconds between successive pane captures while waiting.
    """

    name:              str
    ui_box_tokens:     tuple[str, ...]
    box_wait_timeout:  float = 30.0
    box_poll_interval: float = 1.0

    # ------------------------------------------------------------------ #
    #  Detection helpers
    # ------------------------------------------------------------------ #

    def is_box_visible(self, lines: List[str]) -> bool:
        """
        Return True if any ``ui_box_token`` appears in the last 5 pane lines.

        Checks the bottom of the pane because the input box is always at the
        bottom of the TUI.
        """
        for line in lines[-5:]:
            if any(tok in line for tok in self.ui_box_tokens):
                return True
        return False

    def wait_for_box(
        self,
        capture_fn:  Callable[[int], List[str]],
        is_alive_fn: Callable[[], bool],
        session_name: str = "",
    ) -> bool:
        """
        Block until the UI input box is visible or the timeout elapses.

        Parameters
        ----------
        capture_fn :
            Callable that returns the last N pane lines (TmuxBase.capture).
        is_alive_fn :
            Callable that returns True when the tmux session still exists.
        session_name :
            Used only for log messages.

        Returns
        -------
        bool
            True when the box was detected, False on timeout or dead session.
        """
        deadline = time.time() + self.box_wait_timeout
        while time.time() < deadline:
            if not is_alive_fn():
                logger.warning(
                    "Session '%s': died while waiting for UI box", session_name
                )
                return False
            lines = capture_fn(10)
            if self.is_box_visible(lines):
                logger.debug(
                    "Session '%s': UI box detected (%s profile)",
                    session_name, self.name,
                )
                return True
            time.sleep(self.box_poll_interval)

        logger.warning(
            "Session '%s': UI box not detected after %.0f s (%s profile) — proceeding",
            session_name, self.box_wait_timeout, self.name,
        )
        return False

    # ------------------------------------------------------------------ #
    #  Factory methods
    # ------------------------------------------------------------------ #

    @classmethod
    def from_file(cls, path: Path) -> "AgentProfile":
        """
        Load a profile from a JSON file.

        Expected schema::

            {
              "name":              "gemini",
              "ui_box_tokens":     ["> ", "❯ ", "Type your message"],
              "box_wait_timeout":  30.0,
              "box_poll_interval": 1.0
            }
        """
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            name=data["name"],
            ui_box_tokens=tuple(data.get("ui_box_tokens", [])),
            box_wait_timeout=float(data.get("box_wait_timeout", 30.0)),
            box_poll_interval=float(data.get("box_poll_interval", 1.0)),
        )

    @classmethod
    def for_command(
        cls,
        command: str,
        agents_dir: Optional[Path] = None,
    ) -> "AgentProfile":
        """
        Return an AgentProfile for the given agent CLI command.

        Resolution order:
          1. ``<agents_dir>/<name>.json``  (user-editable override)
          2. Built-in ``_BUILTIN_PROFILES`` table
          3. ``_BUILTIN_PROFILES["_default"]`` fallback

        Parameters
        ----------
        command :
            Full agent command string (e.g. ``"gemini"`` or ``"claude --dangerously-skip-permissions"``).
            Only the first token (the executable name) is used for matching.
        agents_dir :
            Directory to search for ``<name>.json`` overrides.  Typically
            ``<project_root>/agents/``.  Ignored when ``None``.
        """
        name = command.split()[0].lower()

        # 1. JSON override
        if agents_dir is not None:
            json_path = Path(agents_dir) / f"{name}.json"
            if json_path.exists():
                try:
                    profile = cls.from_file(json_path)
                    logger.debug("AgentProfile: loaded '%s' from %s", name, json_path)
                    return profile
                except Exception as exc:
                    logger.warning(
                        "AgentProfile: failed to load %s (%s) — falling back to built-in",
                        json_path, exc,
                    )

        # 2. Built-in table
        if name in _BUILTIN_PROFILES:
            logger.debug("AgentProfile: using built-in profile for '%s'", name)
            return _BUILTIN_PROFILES[name]

        # 3. Default fallback
        logger.debug("AgentProfile: no profile for '%s' — using default", name)
        return _BUILTIN_PROFILES["_default"]


# ---------------------------------------------------------------------------
# Built-in profiles
# ---------------------------------------------------------------------------

_BUILTIN_PROFILES: dict[str, AgentProfile] = {
    "gemini": AgentProfile(
        name="gemini",
        # "Type your message" is the placeholder text inside the Gemini CLI
        # TUI input box — the most reliable indicator that the box is rendered.
        # "> " and "❯ " are fallback prompt tokens for plain-text modes.
        ui_box_tokens=("> ", "❯ ", "Type your message"),
    ),
    "claude": AgentProfile(
        name="claude",
        ui_box_tokens=("> ", "❯ "),
    ),
    "_default": AgentProfile(
        name="_default",
        ui_box_tokens=("> ", "❯ "),
    ),
}
