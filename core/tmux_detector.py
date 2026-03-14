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

probe_pane_state(lines)
-----------------------
Inspects a list of pane lines and returns an AgentState without side-effects.
Used by TmuxManager before sending any command to avoid acting on a stale or
broken session.

States (priority order):
  DEAD                — session does not exist (no lines / caller detected dead)
  QUOTA_EXCEEDED      — gemini reports quota / rate-limit exhaustion
  NEEDS_INTERVENTION  — auth failure, fatal error, unknown blocking prompt
  CONSENT_PENDING     — first-run ToS / consent screen waiting for Ctrl+Y
  STARTING            — gemini launched but not yet at input box
  RUNNING             — normal input-ready state
"""
from __future__ import annotations

import logging
import re
import time
from enum import Enum
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------

class AgentState(str, Enum):
    DEAD                = "dead"
    QUOTA_EXCEEDED      = "quota_exceeded"
    NEEDS_INTERVENTION  = "needs_intervention"
    CONSENT_PENDING     = "consent_pending"
    STARTING            = "starting"
    RUNNING             = "running"


# ---------------------------------------------------------------------------
# Pattern tables  (compiled once at import time)
# ---------------------------------------------------------------------------

# Strings that appear in the last visible lines when gemini is ready for input.
# "> " removed: too broad — matches Gemini TUI input placeholder text
# ("› ", "❯ ") are rich-TUI cursors; "gemini>" is the plain-text fallback
_PROMPT_TOKENS: tuple[str, ...] = ("gemini>", "❯ ")

# Quota / rate-limit indicators (case-insensitive)
_QUOTA_PATTERNS: list[re.Pattern] = [
    re.compile(r, re.IGNORECASE) for r in [
        r"quota.?exceeded",
        r"rate.?limit",
        r"resource.?exhausted",
        r"RESOURCE_EXHAUSTED",
        r"429",
        r"too many requests",
        r"billing",
        r"you have exceeded",
    ]
]

# Consent / ToS screen indicators (case-insensitive)
_CONSENT_PATTERNS: list[re.Pattern] = [
    re.compile(r, re.IGNORECASE) for r in [
        r"terms of service",
        r"privacy policy",
        r"do you agree",
        r"accept.*terms",
        r"press.*ctrl.?y",
        # r"ctrl\+y" removed: matches Gemini's "YOLO ctrl+y" status-bar hint,
        # causing false CONSENT_PENDING whenever yolo mode is active.
        r"\baccept\b.*\bcontinue\b",
        r"consent",
        r"I agree",
    ]
]

# Fatal / intervention-needed indicators (case-insensitive)
_INTERVENTION_PATTERNS: list[re.Pattern] = [
    re.compile(r, re.IGNORECASE) for r in [
        r"authentication.?fail",
        r"permission.?denied",
        r"invalid.?api.?key",
        r"unauthorized",
        r"403",
        r"fatal.?error",
        r"exception",
        r"traceback",
        r"command not found",
        r"cannot find",
    ]
]


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def probe_pane_state(lines: List[str]) -> AgentState:
    """
    Inspect *lines* (recent pane output) and return the most-likely AgentState.

    Checks are ordered by severity: quota > needs_intervention > consent >
    running > starting.  Returns DEAD when lines is empty.
    """
    if not lines:
        return AgentState.DEAD

    joined = "\n".join(lines)

    # ── 1. Quota / rate-limit ────────────────────────────────────────────
    if any(p.search(joined) for p in _QUOTA_PATTERNS):
        logger.debug("probe_pane_state → QUOTA_EXCEEDED")
        return AgentState.QUOTA_EXCEEDED

    # ── 2. Fatal / intervention ──────────────────────────────────────────
    if any(p.search(joined) for p in _INTERVENTION_PATTERNS):
        logger.debug("probe_pane_state → NEEDS_INTERVENTION")
        return AgentState.NEEDS_INTERVENTION

    # ── 3. Consent / ToS screen ──────────────────────────────────────────
    if any(p.search(joined) for p in _CONSENT_PATTERNS):
        logger.debug("probe_pane_state → CONSENT_PENDING")
        return AgentState.CONSENT_PENDING

    # ── 4. Explicit prompt token (ready for input) ───────────────────────
    for line in lines[-3:]:
        if any(tok in line for tok in _PROMPT_TOKENS):
            logger.debug("probe_pane_state → RUNNING (prompt token)")
            return AgentState.RUNNING

    # ── 5. Default: something is in the pane but not yet ready ──────────
    logger.debug("probe_pane_state → STARTING (content present, not ready)")
    return AgentState.STARTING


# ---------------------------------------------------------------------------
# PromptDetector
# ---------------------------------------------------------------------------

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
        capture_fn:    Callable[[int], List[str]],
        is_alive_fn:   Callable[[], bool],
        timeout:       int   = 120,
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
