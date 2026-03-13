"""
Process management utilities.
"""

import logging
import os
import signal
import subprocess
import sys

logger = logging.getLogger(__name__)

def kill_process_tree(proc: subprocess.Popen, name: str) -> None:
    """Kill a subprocess tree cleanly, cross-platform."""
    if proc is None:
        return
    logger.info("Stopping %s (pid %d)...", name, proc.pid)
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                check=False,
            )
        else:
            target_pgid = os.getpgid(proc.pid)
            current_pgid = os.getpgrp()
            if target_pgid == current_pgid:
                proc.terminate()
            else:
                os.killpg(target_pgid, signal.SIGTERM)
    except Exception as exc:
        logger.warning("Could not stop %s: %s", name, exc)
