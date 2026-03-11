# Task: card_04

| Field | Value |
|---|---|
| **Workflow** | cardDealer_evolve |
| **Version** | v1 |
| **Card** | card_04 |
| **Priority** | high |
| **Timestamp** | 2026-03-10T23:30:18.872786 |
| **Tags** | review, quality-gate, strict |

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

## card_04 · Strict Verification Gate

This card is a **hard gate**. Every FAIL must be fixed before writing `![next]!`.

---

### Step 1 — Automated Checks

Run each check; record PASS or FAIL with the exact command output:

**Check 1 — Tests**
```bash
python -m pytest tests/ -v -q
```
PASS: all tests pass, zero failures, zero errors.
FAIL: any test fails → diagnose root cause, fix, re-run.

**Check 2 — Python syntax**
For each `.py` file changed on this branch:
```bash
python -m py_compile <file>
```
PASS: zero output (silent success).
FAIL: syntax error printed → fix before continuing.

**Check 3 — Diff size gate**
```bash
git diff main...HEAD --stat
```
Count total lines added + removed. PASS: total ≤ 150. FAIL: total > 150 → reduce scope.

**Check 4 — Files touched count**
From the diff stat, count distinct files changed.
PASS: ≤ 3 files. FAIL: > 3 files → revert excess changes.

**Check 5 — No debug output**
```bash
git diff main...HEAD
```
Search for: `print(`, `console.log(`, `debugger`, `pdb.set_trace`, `breakpoint()`.
PASS: none found in production code paths (test files are exempt).
FAIL: any found → remove before continuing.

**Check 6 — No secrets**
In the same diff, grep for: `password`, `secret`, `api_key`, `token =`, `AWS_`, `-----BEGIN`.
PASS: none found (test fixture dummy values are exempt if clearly labeled).
FAIL: any real credential → remove immediately.

---

### Step 2 — Manual Checklist

Verify each item against the diff; record PASS / FAIL / N-A:

7. All acceptance criteria from `EVOLVE_SPRINT.md` are satisfied (check each one explicitly).
8. The change does not introduce new hardcoded magic values (numbers, IP strings, port literals).
9. Every new or modified function has a type annotation on its return value (Python) or explicit
   parameter types (TypeScript).
10. No bare `except:` or `except Exception: pass` added without a log statement.
11. No commented-out code blocks added (dead code).
12. The test added in card_03 actually exercises the changed code path (not just a placeholder).

---

### Fix Loop

For each FAIL: fix in place, re-run the specific check, confirm PASS before moving on.
Do NOT write `![next]!` while any check is FAIL.

---

### Write EVOLVE_REVIEW.md

```
# Evolve Review

## Automated Checks
| # | Check | Command | Result | Notes |
|---|-------|---------|--------|-------|
| 1 | Tests | pytest ... | PASS/FAIL | ... |
| 2 | Syntax | py_compile | PASS/FAIL | ... |
| 3 | Diff size | git diff --stat | PASS/FAIL | N lines |
| 4 | Files touched | git diff --stat | PASS/FAIL | N files |
| 5 | Debug output | grep | PASS/FAIL | ... |
| 6 | Secrets | grep | PASS/FAIL | ... |

## Manual Checklist
| # | Item | Result | Notes |
|---|------|--------|-------|
| 7 | Acceptance criteria | PASS/FAIL | ... |
| 8 | No new magic values | PASS/FAIL | ... |
| 9 | Type annotations | PASS/FAIL | ... |
|10 | Error handling | PASS/FAIL | ... |
|11 | No dead code | PASS/FAIL | ... |
|12 | Test exercises change | PASS/FAIL | ... |

## Issues Found and Fixed
<list any FAILs and the fix applied>

## Final Verdict
**APPROVED** or **NEEDS_REWORK**
```

The verdict MUST be **APPROVED** before writing `![next]!`.

> **HOUSEKEEPING REMINDER**: Before finishing this task, take a moment to DRY up any duplicated code you encounter and tidy the folder structure. Remove dead code, consolidate shared logic, and ensure clean imports.

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

