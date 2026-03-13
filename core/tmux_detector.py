"""
Readiness detection for AI agent CLI sessions.

PromptDetector polls a tmux pane using three strategies (in priority order):

  A. Explicit prompt token  — looks for 'gemini>', '> ', or '❯ ' in the last
                              few visible lines. Fastest when the CLI renders a
                              text prompt.

  B. Stable pane output     — compares successive captures 2 s apart. When the
                              TUI input box is rendered and idle, the pane stops
                              changing. Reliable for rich TUI apps that do not
                              emit a plain-text prompt.

  C. Timeout fallback       — if neither A nor B fires within `timeout` seconds,
                              log a warning and return False so the caller can
                              decide whether to proceed anyway.
"""
from __future__ import annotations

import logging
import time
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

# Strings that appear in the last visible lines when gemini is ready for input.
_PROMPT_TOKENS = ("gemini>", "> ", "❯ ")


class PromptDetector:
    """
    Detects when an AI agent CLI is ready for input by reading live pane output.

    Parameters
    ----------
    capture_fn :
        Callable that returns the last N pane lines (from TmuxBase.capture).
    is_alive_fn :
        Callable that returns True if the session still exists.
    timeout :
        Maximum seconds to wait before giving up (safety ceiling only).
    poll_interval :
        Seconds between pane reads (default 2).
    prompt_tokens :
        Tuple of strings to look for in the last visible lines.
    """

    def __init__(
        self,
        capture_fn:   Callable[[int], List[str]],
        is_alive_fn:  Callable[[], bool],
        timeout:      int = 120,
        poll_interval: float = 2.0,
        prompt_tokens: tuple = _PROMPT_TOKENS,
    ) -> None:
        self._capture      = capture_fn
        self._is_alive     = is_alive_fn
        self._timeout      = timeout
        self._poll         = poll_interval
        self._tokens       = prompt_tokens

    def wait(self, session_name: str = "") -> bool:
        """
        Block until a ready signal is detected or the timeout is reached.

        Returns True if ready was detected, False if timed out.
        """
        deadline   = time.time() + self._timeout
        prev_snap: Optional[str] = None

        while time.time() < deadline:
            time.sleep(self._poll)

            if not self._is_alive():
                logger.warning("Session '%s' died during readiness wait", session_name)
                return False

            lines = self._capture(10)

            # ── Strategy A: explicit prompt token ────────────────────────
            for line in lines[-3:]:
                if any(tok in line for tok in self._tokens):
                    logger.info(
                        "Session '%s': ready (explicit prompt detected)", session_name
                    )
                    return True

            # ── Strategy B: stable pane (TUI input box rendered) ─────────
            snap = "\n".join(lines)
            if prev_snap is not None and snap == prev_snap and snap:
                logger.info(
                    "Session '%s': ready (stable pane / input box visible)", session_name
                )
                return True
            prev_snap = snap

        logger.warning(
            "Session '%s': ready signal not seen after %ds — proceeding anyway",
            session_name, self._timeout,
        )
        return False
