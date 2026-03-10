"""
Custom exceptions for the Agent Instruction Engine.
Centralizes all error types for consistent error handling across modules.
"""


class CardEngineError(Exception):
    """Base exception for all CardDealer engine errors."""
    pass


class CardNotFoundError(CardEngineError):
    """Raised when a card ID cannot be resolved in the workflow."""

    def __init__(self, card_id: str, workflow: str = ""):
        self.card_id = card_id
        self.workflow = workflow
        msg = f"Card '{card_id}' not found"
        if workflow:
            msg += f" in workflow '{workflow}'"
        super().__init__(msg)


class WorkflowValidationError(CardEngineError):
    """Raised when a workflow's structure or card schema is invalid."""

    def __init__(self, workflow: str, detail: str = ""):
        self.workflow = workflow
        msg = f"Workflow '{workflow}' validation failed"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


class TaskFileError(CardEngineError):
    """Raised when the current_task.md file cannot be read or written."""
    pass


class InvalidWorkflowPathError(CardEngineError):
    """Raised on path traversal attempt (e.g., '../../' in workflow name)."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Invalid workflow path (potential traversal): {path}")
