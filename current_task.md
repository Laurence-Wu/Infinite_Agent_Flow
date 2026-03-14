# Task: card_01

| Field | Value |
|---|---|
| **Workflow** | sample_workflow |
| **Version** | v1 |
| **Card** | card_01 |
| **Priority** | high |
| **Timestamp** | 2026-03-14T16:47:36.757361 |
| **Tags** | setup, infrastructure |

---

**IMPORTANT**: Follow the instructions in this file exactly as written. Ignore task numbering — just implement what is described below.

**WORKSPACE BOUNDARY**: You must only read and modify files within `C:\Users\MSI\Desktop\WinCoding\CardDealer`. Do NOT access, create, or modify any files outside this directory. All paths in your work must be relative to or within this workspace.

```
╔══════════════════════════════════════════════════════════════╗
║              AGENT OPERATING PROTOCOL                       ║
╚══════════════════════════════════════════════════════════════╝
```

You are an autonomous coding agent inside a continuous task engine.
Follow this protocol on every card — no exceptions:

**STEP 1 — READ**
Read the entire task below. Understand the full scope before acting.

**STEP 2 — IMPLEMENT**
Implement everything the task describes. No skipping. No partial work.
Do not narrate your process or explain what you are about to do. Just do it.

**STEP 3 — RECORD  ⚠️ WRITE INTO THE FILE ON DISK**
When done, open `current_task.md` with your file-edit tool and **append**
this exact block at the end of the file:

```markdown
## Summary
- **Files changed**: <every file created or modified>
- **Commands run**: <every shell command executed>
- **Tests**: <pass/fail counts, or 'n/a'>
- **Git**: <commit hash, or 'no commit'>
- **Notes**: <anything critical for the next agent to know>

![next]!
```

> ⚠️ **WARNING**: This block MUST be physically written into `current_task.md`
> on disk using your file-edit tool.
> Do **NOT** output it in chat — chat output is invisible to the engine.
> The engine watches the file. If `![next]!` is not in the file, the loop stalls.

**STEP 4 — WAIT**
Wait 5 seconds after saving. The engine will replace `current_task.md`
with the next task automatically. Then repeat from Step 1.

---

**PYTHON VIRTUAL ENVIRONMENT**: All Python work in this task must be done inside the isolated virtual environment at `C:\Users\MSI\Desktop\WinCoding\CardDealer\.venv`.

**Setup** (run once if `.venv` does not exist yet):
```
python -m venv C:\Users\MSI\Desktop\WinCoding\CardDealer\.venv
```

**Activate** before running any Python or `pip` command:
```
C:\Users\MSI\Desktop\WinCoding\CardDealer\.venv\Scripts\activate
```

**Install packages** only inside the venv:
```
pip install <package>           # after activation
pip freeze > requirements.txt   # to record dependencies
```

**Rules**:
- Never use `pip install` without first activating the venv.
- Never modify or install to the system Python.
- If the venv is missing or broken, delete `.venv` and recreate it.
- Always run experiments with the venv Python: `C:\Users\MSI\Desktop\WinCoding\CardDealer\.venv\Scripts\python.exe`

## Current Task

Think about this step by step. Break the problem down into smaller sub-tasks and address each one carefully.

Set up the project directory structure.

Create the following folders inside the workspace:
- src/
- tests/
- docs/

Verify each folder exists after creation.

![stop]! (append this line when done)

> **GIT BRANCH POLICY**: This task involves high-risk changes. Before making any modifications, create a new git branch from the current branch using: `git checkout -b card/<card_id>`. Commit your changes to this branch. Do NOT push or merge — leave that for review.

---
**COMPLETION CHECKLIST** — before you finish:

1. All task steps above are fully implemented.
2. Open `current_task.md` with your file-edit tool and append:
   - `## Summary` with bullet points:
     - Files changed, commands run, test results, git commit hash, notes.
   - Then the next-card marker on its own line:
     exclamation + open-bracket + the word **next** + close-bracket + exclamation
     (the seven characters  ! [ n e x t ] !  with no spaces — written into the file).
3. Do **not** write the marker in chat — it must land in the file on disk.

