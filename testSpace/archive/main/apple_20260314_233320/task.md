# Task: banana

| Field | Value |
|---|---|
| **Workflow** | jobscrap_v2 |
| **Version** | v1 |
| **Card** | banana |
| **Priority** | normal |
| **Timestamp** | 2026-03-14T20:03:28.640973 |
| **Tags** | feature, discover |

---

**IMPORTANT**: Follow the instructions in this file exactly as written. Ignore task numbering — just implement what is described below.

**WORKSPACE BOUNDARY**: You must only read and modify files within `/home/xwu/agent_playground/Infinite_Agent_Flow/testSpace`. Do NOT access, create, or modify any files outside this directory. All paths in your work must be relative to or within this workspace.

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

**PYTHON VIRTUAL ENVIRONMENT**: All Python work in this task must be done inside the isolated virtual environment at `/home/xwu/agent_playground/Infinite_Agent_Flow/testSpace\.venv`.

**Setup** (run once if `.venv` does not exist yet):
```
python -m venv /home/xwu/agent_playground/Infinite_Agent_Flow/testSpace\.venv
```

**Activate** before running any Python or `pip` command:
```
/home/xwu/agent_playground/Infinite_Agent_Flow/testSpace\.venv\Scripts\activate
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
- Always run experiments with the venv Python: `/home/xwu/agent_playground/Infinite_Agent_Flow/testSpace\.venv\Scripts\python.exe`

## Current Task

## f1 · Discover and Plan the Next Feature Sprint

Workspace: `C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room`

### Goal
Select the single highest-impact unshipped improvement, research its feasibility,
and write a complete `SPRINT_DECISION.md` so f2 can start immediately.

### Step 1 — Gather Context
1. Read `EVOLUTION_BACKLOG.md` (create if missing — populate in step 3)
2. Read `EVOLUTION_LOG.md` — know what has already shipped
3. Read the last 3 `### Analysis` sections from `ops_log.md`

### Step 2 — Select Highest-Priority Item
Priority ranking:
  **P0** — breaks production or causes zero yield (fix immediately)
  **P1** — reduces manual work, improves reliability, or fixes alert failures
  **P2** — expands scraper coverage or adds a new data source
  **P3** — nice-to-have quality improvements

Common high-value P1/P2 items to consider if backlog is empty:
  - Integrate async scraping (fetch multiple sources concurrently)
  - Build Handshake scraper (Selenium-based) to automate s4
  - Add WayUp API integration
  - Auto-refresh companies.csv from a curated remote source
  - Add Discord notification (webhook) for S-tier alerts
  - Add job deduplication by title+company (catch same role on multiple boards)
  - Build a CLI dashboard (rich) showing live pipeline stats
  - Scheduled auto-run via Windows Task Scheduler integration guide

### Step 3 — Feasibility Check
Before writing SPRINT_DECISION.md:
  - Read the relevant source files
  - Confirm the change fits in ~200 lines of new code
  - List exactly which files change

### Step 4 — Write SPRINT_DECISION.md
```markdown
# Sprint Decision

## Selected: <feature title>
## Priority: <P0/P1/P2/P3>
## Branch: feat/<kebab-case-name>

## Problem
<What is broken or missing — cite specific ops_log data>

## Proposed Solution
<3-5 sentence implementation plan — be concrete>

## Files to Change
- <file1.py>: <what changes>
- <file2.py>: <what changes>

## Acceptance Criteria
- [ ] <verifiable criterion 1>
- [ ] <verifiable criterion 2>
- [ ] <verifiable criterion 3>
- [ ] All existing tests still pass
- [ ] New tests cover the changed code

## Out of Scope
<What you will NOT do in this sprint>
```

### Step 5 — Seed Backlog if Missing
If `EVOLUTION_BACKLOG.md` was missing or empty: create it with the top 5
improvements identified from ops_log pain points and the suggestions in step 2.


> **HOUSEKEEPING REMINDER**: Before finishing this task, take a moment to DRY up any duplicated code you encounter and tidy the folder structure. Remove dead code, consolidate shared logic, and ensure clean imports.

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

