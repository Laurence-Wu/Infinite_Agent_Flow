# Task: apple

| Field | Value |
|---|---|
| **Workflow** | jobscrap_v2 |
| **Version** | v1 |
| **Card** | apple |
| **Priority** | normal |
| **Timestamp** | 2026-03-14T20:01:12.717962 |
| **Tags** | ops, commit |

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

## s8 · Commit Ops Changes

Workspace: `C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room`

### Goal
Run the full test suite, stage only safe ops files (never credentials),
commit with the ops convention, push, and trim the seen_jobs cache if bloated.

### Step 1 — Final Test Gate
```
cd C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room
.venv\Scripts\activate
.venv\Scripts\python.exe -m pytest tests/ -v
```
100% pass required. If any test fails: fix it first, then come back here.

### Step 2 — Stage Only Safe Files
**NEVER** stage: `config.json`, `.env`, `.env.local`, `*.key`, `*.pem`
Safe to stage:
```
git add ops_log.md EVOLUTION_LOG.md EVOLUTION_BACKLOG.md
git add keywords/ src/ tests/ requirements.txt
git add manually_added_jobs.json  # if it changed
```
Only add files that were actually modified this cycle. Check with `git diff --name-only`.

### Step 3 — Commit
Use host-shell date style:
- Linux/macOS: `git commit -m "ops: daily run and tuning $(date +%Y-%m-%d)"`
- PowerShell: `git commit -m "ops: daily run and tuning $(Get-Date -Format yyyy-MM-dd)"`

### Step 4 — Push
```
git push origin main
```

### Step 5 — Trim seen_jobs Cache
If `seen_jobs_orchestrator.json` has more than 500 entries:
```python
import json
import pathlib

f = pathlib.Path(r"C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room/seen_jobs_orchestrator.json")
items = json.loads(f.read_text(encoding="utf-8"))
if len(items) > 500:
    items = items[-200:]  # keep last 200
    f.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"Trimmed to {len(items)} entries")
```
Then stage and commit the cache trim only if the file changed.

### Step 6 — Confirm
```
git log --oneline -5
git status
```


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

