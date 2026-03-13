"""
Central configuration for the Agent Instruction Engine.
All tunable parameters live here as a single dataclass.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EngineConfig:
    """
    Immutable-ish configuration passed to every engine component.

    Attributes:
        workspace_path:         Root directory where current_task.md and archive live.
        workflows_path:         Root directory containing workflow definitions.
        archive_dir:            Subdirectory name inside workspace for finished tasks.
        current_task_filename:  Name of the active task markdown file.
        flask_host:             Bind host for the Flask dashboard (dashboard owner only).
    """

    workspace_path: str = "./workspace"
    workflows_path: str = "./workflows"
    archive_dir: str = "archive"
    current_task_filename: str = "current_task.md"
    flask_host: str = "127.0.0.1"
    # Agent session management
    agent_command: str = "gemini"   # CLI command to launch the AI agent (e.g. "claude", "aider")
    agent_startup_wait: int = 20    # seconds to wait for agent to start before sending AGENT_LOOP.md

    # ----- derived paths (set in __post_init__) -----
    _workspace: Path = field(init=False, repr=False)
    _workflows: Path = field(init=False, repr=False)

    def __post_init__(self):
        self._workspace = Path(self.workspace_path).resolve()
        self._workflows = Path(self.workflows_path).resolve()
        # Ensure critical directories exist
        self._workspace.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)

    # ----- convenience properties -----

    @property
    def task_file(self) -> Path:
        """Full path to the current task markdown file."""
        return self._workspace / self.current_task_filename

    @property
    def archive_path(self) -> Path:
        """Full path to the archive directory."""
        return self._workspace / self.archive_dir

    @property
    def master_summary_file(self) -> Path:
        """Full path to the master summary markdown file."""
        return self.archive_path / "master_summary.md"

    @property
    def resolved_workspace(self) -> Path:
        return self._workspace

    @property
    def resolved_workflows(self) -> Path:
        return self._workflows
