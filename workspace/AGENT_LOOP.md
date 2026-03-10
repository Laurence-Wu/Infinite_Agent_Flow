# Workspace Agent — Operating Protocol

You are an autonomous agent. Your only job is to implement whatever
`current_task.md` says, completely and correctly, then signal done.

---

## What to do

1. **Read** `current_task.md`. That file contains your assignment.

2. **Implement** everything described in it. Do not skip steps.
   Do not explain what you are about to do. Just do it.

3. **When finished**, add this block at the end of `current_task.md`:

   ```markdown
   ## Summary
   <one or two sentences describing what you actually did>

   ![next]!
   ```

4. **Wait 5 seconds**, then read `current_task.md` again —
   it will contain a new assignment. Repeat from step 2.

---

## Rules

- Only touch files inside the workspace directory.
- Never narrate, describe the protocol, or output meta-commentary.
  Your output is code and file changes, not explanations of your process.
- Use `.venv\Scripts\python.exe` for all Python execution.

---

## Python venv

Create once if missing:
```
python -m venv .venv
```

Activate before any `pip` or `python` command:
```
.venv\Scripts\activate
```
