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
        """Append the completion reminder footer.
        Reinforces the write-to-disk requirement and the structured Summary format.
        IMPORTANT: The token is described in words so the planner regex won't
        false-match this instruction text inside the dealt card."""
        self._suffixes.append(
            "\n\n---\n"
            "**COMPLETION CHECKLIST** — before you finish:\n\n"
            "1. All task steps above are fully implemented.\n"
            "2. Open `current_task.md` with your file-edit tool and append:\n"
            "   - `## Summary` with bullet points:\n"
            "     - Files changed, commands run, test results, git commit hash, notes.\n"
            "   - Then the next-card marker on its own line:\n"
            "     exclamation + open-bracket + the word **next** + close-bracket + exclamation\n"
            "     (the seven characters  ! [ n e x t ] !  with no spaces — written into the file).\n"
            "3. Do **not** write the marker in chat — it must land in the file on disk.\n"
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

    def add_git_safety(self) -> "InstructionWrapper":
        """Inject a git interactive-editor safety warning.
        Reminds the agent that git operations (commit, rebase, merge) can open
        interactive editors that block the session. Use non-interactive flags or
        press Ctrl+X to exit nano/pico without saving."""
        self._suffixes.append(
            "\n\n> **GIT SAFETY — NON-INTERACTIVE MODE**: Some git commands open an "
            "interactive editor (e.g. `git commit` without `-m`, `git rebase -i`, "
            "`git merge` with conflicts). This will **block the agent session** and "
            "require manual intervention.\n\n"
            "> **Always use non-interactive flags**:\n"
            "> - `git commit -m \"message\"` — never bare `git commit`\n"
            "> - `git merge --no-edit` — accept the default merge message\n"
            "> - `git rebase --abort` if an interactive rebase accidentally starts\n"
            "> - If an editor opens unexpectedly, press **Ctrl+X** to exit nano/pico "
            "without saving, then retry with a non-interactive flag.\n"
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

    def add_venv_directive(self, workspace_path: str) -> "InstructionWrapper":
        """Inject venv creation and management instructions (Windows).
        Tells the agent to use an isolated virtual environment at
        {workspace}\\.venv for all Python experimentation, keeping the
        system Python untouched."""
        self._prefixes.append(
            f"**PYTHON VIRTUAL ENVIRONMENT**: All Python work in this task must be "
            f"done inside the isolated virtual environment at `{workspace_path}\\.venv`.\n\n"
            f"**Setup** (run once if `.venv` does not exist yet):\n"
            f"```\n"
            f"python -m venv {workspace_path}\\.venv\n"
            f"```\n\n"
            f"**Activate** before running any Python or `pip` command:\n"
            f"```\n"
            f"{workspace_path}\\.venv\\Scripts\\activate\n"
            f"```\n\n"
            f"**Install packages** only inside the venv:\n"
            f"```\n"
            f"pip install <package>           # after activation\n"
            f"pip freeze > requirements.txt   # to record dependencies\n"
            f"```\n\n"
            f"**Rules**:\n"
            f"- Never use `pip install` without first activating the venv.\n"
            f"- Never modify or install to the system Python.\n"
            f"- If the venv is missing or broken, delete `.venv` and recreate it.\n"
            f"- Always run experiments with the venv Python: "
            f"`{workspace_path}\\.venv\\Scripts\\python.exe`\n\n"
        )
        return self

    def add_infinite_loop_directive(self) -> "InstructionWrapper":
        """Inject the full agent operating protocol as a prominent banner.
        Self-contained: every card carries the complete loop instructions,
        process-recording rules, and the write-to-disk warning."""
        self._prefixes.insert(0,
            "```\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║              AGENT OPERATING PROTOCOL                       ║\n"
            "╚══════════════════════════════════════════════════════════════╝\n"
            "```\n\n"
            "You are an autonomous coding agent inside a continuous task engine.\n"
            "Follow this protocol on every card — no exceptions:\n\n"
            "**STEP 1 — READ**\n"
            "Read the entire task below. Understand the full scope before acting.\n\n"
            "**STEP 2 — IMPLEMENT**\n"
            "Implement everything the task describes. No skipping. No partial work.\n"
            "Do not narrate your process or explain what you are about to do. Just do it.\n\n"
            "**STEP 3 — RECORD  ⚠️ WRITE INTO THE FILE ON DISK**\n"
            "When done, open `current_task.md` with your file-edit tool and **append**\n"
            "this exact block at the end of the file:\n\n"
            "```markdown\n"
            "## Summary\n"
            "- **Files changed**: <every file created or modified>\n"
            "- **Commands run**: <every shell command executed>\n"
            "- **Tests**: <pass/fail counts, or 'n/a'>\n"
            "- **Git**: <commit hash, or 'no commit'>\n"
            "- **Notes**: <anything critical for the next agent to know>\n\n"
            "![next]!\n"
            "```\n\n"
            "> ⚠️ **WARNING**: This block MUST be physically written into `current_task.md`\n"
            "> on disk using your file-edit tool.\n"
            "> Do **NOT** output it in chat — chat output is invisible to the engine.\n"
            "> The engine watches the file. If `![next]!` is not in the file, the loop stalls.\n\n"
            "**STEP 4 — WAIT**\n"
            "Wait 5 seconds after saving. The engine will replace `current_task.md`\n"
            "with the next task automatically. Then repeat from Step 1.\n\n"
            "---\n\n"
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
