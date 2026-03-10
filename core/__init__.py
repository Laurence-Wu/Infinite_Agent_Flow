"""
Core module — DRY foundations for the Agent Instruction Engine.

Exports:
    BaseCard, BaseWorkflow   — abstract data models
    InstructionWrapper       — builder-pattern prompt composer
    StateManager             — thread-safe shared state
    EngineConfig             — central configuration
    Exceptions               — CardNotFoundError, WorkflowValidationError, etc.
"""

from .base_card import BaseCard, BaseWorkflow
from .config import EngineConfig
from .exceptions import (
    CardEngineError,
    CardNotFoundError,
    InvalidWorkflowPathError,
    TaskFileError,
    WorkflowValidationError,
)
from .state_manager import StateManager
from .wrappers import InstructionWrapper

__all__ = [
    # Data models
    "BaseCard",
    "BaseWorkflow",
    # Config
    "EngineConfig",
    # State
    "StateManager",
    # Wrappers
    "InstructionWrapper",
    # Exceptions
    "CardEngineError",
    "CardNotFoundError",
    "InvalidWorkflowPathError",
    "TaskFileError",
    "WorkflowValidationError",
]
