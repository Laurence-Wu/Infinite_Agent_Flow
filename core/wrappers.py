"""
InstructionWrapper — Builder-pattern prompt composer.

The Dealer reads card metadata and dynamically constructs the final
instruction by chaining wrapper methods.  Each .add_*() returns self
for fluent chaining; .wrap(instruction) applies all transforms in order.

Example
-------
>>> wrapper = InstructionWrapper()
>>> final = (wrapper
...     .add_step_by_step()
...     .add_stop_token_footer()
...     .add_custom("Be concise.")
...     .wrap(card.instruction))
"""

from __future__ import annotations

from typing import Callable, List


class InstructionWrapper:
    """Composable, order-preserving instruction transformer."""

    def __init__(self):
        self._prefixes: List[str] = []
        self._suffixes: List[str] = []
        self._transforms: List[Callable[[str], str]] = []

    # ------------------------------------------------------------------ #
    #  Built-in wrapper methods (all return self for chaining)
    # ------------------------------------------------------------------ #

    def add_step_by_step(self) -> "InstructionWrapper":
        """Prepend a 'think step by step' preamble."""
        self._prefixes.append(
            "Think about this step by step. Break the problem down "
            "into smaller sub-tasks and address each one carefully.\n\n"
        )
        return self

    def add_stop_token_footer(self) -> "InstructionWrapper":
        """Append the standard stop-token instruction.
        IMPORTANT: The instruction describes the token format without
        writing it literally, so the planner's regex won't false-match
        the instruction text in the dealt card."""
        self._suffixes.append(
            "\n\n---\n"
            "Read and follow the above instruction step by step. "
            "When finished implementation, you should add the summary "
            "and then output the completion marker: exclamation, open-bracket, "
            "the word stop, close-bracket, exclamation (e.g. the five characters "
            "! [ s t o p ] !) at the end of the "
            "markdown generation, and your current task is finished."
        )
        return self

    def add_dry_reminder(self) -> "InstructionWrapper":
        """Inject a DRY-code and tidy-folder-structure reminder.
        Used by the Dealer every N cards to keep the workspace clean."""
        self._suffixes.append(
            "\n\n> **HOUSEKEEPING REMINDER**: Before finishing this task, take a moment to "
            "DRY up any duplicated code you encounter and tidy the folder structure. "
            "Remove dead code, consolidate shared logic, and ensure clean imports."
        )
        return self

    def add_follow_task_instruction(self) -> "InstructionWrapper":
        """Inject the standard 'follow this task file' instruction.
        Always added by the engine to every card."""
        self._prefixes.insert(0,
            "**IMPORTANT**: Follow the instructions in this file exactly as written. "
            "Ignore task numbering — just implement what is described below.\n\n"
        )
        return self

    def add_workspace_boundary(self, workspace_path: str) -> "InstructionWrapper":
        """Constrain the agent to only work within the workspace directory.
        Prevents accessing or modifying files outside the project boundary."""
        self._prefixes.insert(1,
            f"**WORKSPACE BOUNDARY**: You must only read and modify files within "
            f"`{workspace_path}`. Do NOT access, create, or modify any files "
            f"outside this directory. All paths in your work must be relative to "
            f"or within this workspace.\n\n"
        )
        return self

    def add_branch_policy(self) -> "InstructionWrapper":
        """Inject a git branch policy for high-risk changes.
        Tells the agent to create a feature branch before making risky modifications."""
        self._suffixes.append(
            "\n\n> **GIT BRANCH POLICY**: This task involves high-risk changes. "
            "Before making any modifications, create a new git branch from the current "
            "branch using: `git checkout -b card/<card_id>`. Commit your changes to "
            "this branch. Do NOT push or merge — leave that for review."
        )
        return self

    def add_infinite_loop_directive(self) -> "InstructionWrapper":
        """Inject the infinite-loop commitment directive.
        Tells the agent it operates inside a perpetual autonomous loop and
        must never self-terminate, skip tasks, or exit the cycle voluntarily."""
        self._prefixes.insert(0,
            "**YOU ARE OPERATING INSIDE AN INFINITE AUTONOMOUS LOOP.** "
            "This loop runs forever until the system is explicitly shut down externally. "
            "You must complete every task assigned to you fully and correctly — "
            "no skipping, no partial work, no self-imposed stopping. "
            "Do not attempt to exit, pause, or break the loop under any circumstance. "
            "Your sole directive is to execute the current task to completion, "
            "signal done with the stop token, and await the next card. "
            "The loop continues after you. Commit to it.\n\n"
        )
        return self

    def add_envelope(self) -> "InstructionWrapper":
        """Wrap with the standard task envelope header."""
        self._prefixes.append("## Current Task\n\n")
        return self

    def add_custom(self, text: str, *, position: str = "prefix") -> "InstructionWrapper":
        """
        Add arbitrary text as a prefix or suffix.

        Parameters
        ----------
        text : str
            The text to inject.
        position : str
            "prefix" (before instruction) or "suffix" (after instruction).
        """
        if position == "prefix":
            self._prefixes.append(text + "\n\n")
        else:
            self._suffixes.append("\n\n" + text)
        return self

    def add_transform(self, fn: Callable[[str], str]) -> "InstructionWrapper":
        """
        Register an arbitrary transformation function that will
        be applied to the instruction text after prefix/suffix assembly.
        """
        self._transforms.append(fn)
        return self

    # ------------------------------------------------------------------ #
    #  Assembly
    # ------------------------------------------------------------------ #

    def wrap(self, instruction: str) -> str:
        """
        Apply all registered prefixes, suffixes, and transforms
        to produce the final instruction string.
        """
        parts = self._prefixes + [instruction] + self._suffixes
        result = "".join(parts)

        for fn in self._transforms:
            result = fn(result)

        return result

    def reset(self) -> "InstructionWrapper":
        """Clear all registered wrappers (reuse the same instance)."""
        self._prefixes.clear()
        self._suffixes.clear()
        self._transforms.clear()
        return self

    def __repr__(self) -> str:
        return (
            f"InstructionWrapper("
            f"prefixes={len(self._prefixes)}, "
            f"suffixes={len(self._suffixes)}, "
            f"transforms={len(self._transforms)})"
        )
