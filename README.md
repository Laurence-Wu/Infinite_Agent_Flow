# CardDealer

Card-driven orchestration engine for autonomous AI agent loops.

---

## Install

```bash
git clone <repo> && cd CardDealer
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

---

## Start

```bash
# Dashboard owner (Flask :5000 + Next.js :3000)
python orchestrator.py --workspace ./workspace --workflow sample_workflow --version v1

# Attach a second agent to the same dashboard
python orchestrator.py --workspace ./workspace2 --workflow jobscrap_v2 --version v1 \
  --server http://localhost:5000 --agent-id agent_1
```

---

## Start with AI Agent (tmux)

```bash
# Auto-start the agent session when the orchestrator launches
python orchestrator.py --workspace ./workspace --workflow sample_workflow --version v1 \
  --auto-start

# Use a different agent (default: gemini)
python orchestrator.py --workspace ./workspace --workflow sample_workflow --version v1 \
  --agent-command "claude" --auto-start

# Custom session name
python orchestrator.py --workspace ./workspace --workflow sample_workflow --version v1 \
  --session-name my_session --auto-start
```

Or use the shell scripts directly:

```bash
# Linux / macOS / WSL
bash scripts/start_agent.sh ./workspace my_session gemini 20
bash scripts/stop_agent.sh my_session
bash scripts/restart_agent.sh ./workspace my_session gemini 20

# Windows (requires WSL2 + tmux)
scripts\start_agent.bat .\workspace my_session
scripts\stop_agent.bat my_session
```

Attach to the running session:

```bash
tmux attach -t my_session
```

The session tracker on the dashboard (`localhost:3000`) shows live pane output and Start / Stop / Restart controls.

---

## Expose over ngrok

```bash
# Install ngrok, then authenticate once
ngrok config add-authtoken <your-token>

# Start with ngrok tunnel (basic-auth protected)
python orchestrator.py --workspace ./workspace --workflow sample_workflow --version v1 \
  --ngrok-auth "user:password"
```

The log prints the public URL:

```
[INFO] ngrok public URL: https://abc123.ngrok-free.app  (basic-auth protected)
```

Attach a remote agent through ngrok:

```bash
python orchestrator.py --workspace ./workspace2 --workflow jobscrap_v2 --version v1 \
  --agent-id agent_remote \
  --server "https://user:password@abc123.ngrok-free.app"
```

---

## Workflow card format

```json
{
  "id": "card_01",
  "title": "Task title",
  "instructions": "What the agent must do.",
  "next_card": "card_02",
  "branches": {
    "retry": "card_01",
    "done":  "card_02"
  }
}
```

Cards live at `workflows/<name>/<version>/<id>.json`. Never modified by the engine.

---

## Completion tokens

The agent appends to `current_task.md`:

```
## Summary
One sentence summary.

![next]!              # advance to next_card
![next:done]!         # follow the "done" branch
![next:retry]!        # follow the "retry" branch
```

---

## API

| Method | Path | Body |
| ------ | ---- | ---- |
| GET | `/api/agents` | — |
| GET | `/api/agent/<id>` | — |
| POST | `/api/agent/<id>/pause` | — |
| POST | `/api/agent/<id>/resume` | — |
| POST | `/api/agent/<id>/stop` | — |
| POST | `/api/agent/<id>/deal` | — |
| POST | `/api/agents` | `{workspace, workflow, version}` |
| GET | `/api/archive` | — |
| GET | `/api/session` | — |
| POST | `/api/session/start` | — |
| POST | `/api/session/stop` | — |
| POST | `/api/session/restart` | — |

---

## Config (`EngineConfig`)

| Field | Default |
| ----- | ------- |
| `workspace_path` | `./workspace` |
| `workflows_path` | `./workflows` |
| `archive_dir` | `archive` |
| `current_task_filename` | `current_task.md` |
| `flask_host` | `127.0.0.1` |
| `agent_command` | `gemini` |
| `agent_startup_wait` | `20` |
