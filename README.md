# CardDealer

Card-driven orchestration engine for autonomous AI agent loops.

Two distinct concepts:

- **Card Dealer** — the workflow runner that reads cards, tracks progress, and drives the AI
- **Agent** — the AI process (Gemini, Claude, etc.) running inside a tmux session

---

## Install

```bash
git clone <repo> && cd CardDealer
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

---

## Quick Start

Fill in [configure_user.json](configure_user.json), then:

```bash
# Linux / macOS / WSL
bash scripts/start.sh        # primary agent (workspace_1)
bash scripts/start.sh 2      # secondary agent (workspace_2)

# Windows
scripts\start.bat
scripts\start.bat 2
```

The script reads `configure_user.json` and passes `--ngrok-auth`, `--workspace`, `--workflow`, `--port`, and `--agent-id` to `orchestrator.py` automatically.

Opens the dashboard at `http://localhost:3000`.

---

## Start with AI Agent (tmux)

```bash
# Auto-start gemini in a tmux session when the orchestrator launches
python orchestrator.py --workspace ./workspace --workflow sample_workflow \
  --auto-start

# Use a different agent
python orchestrator.py --workspace ./workspace --workflow sample_workflow \
  --agent-command "claude" --auto-start

# Custom tmux session name
python orchestrator.py --workspace ./workspace --workflow sample_workflow \
  --session-name my_session --auto-start
```

The **Agent panel** in the dashboard shows live pane output (streamed via SSE, ~1 s latency)
and provides **Start / Pause / Stop / Restart** controls.

Attach to the running session directly:

```bash
tmux attach -t my_session        # Linux / macOS / WSL
wsl tmux attach -t my_session    # Windows PowerShell
```

---

## Expose over ngrok

```bash
# Authenticate ngrok once
ngrok config add-authtoken <your-token>

# Start with a public ngrok tunnel (HTTP basic-auth protected)
python orchestrator.py --workspace ./workspace --workflow sample_workflow \
  --ngrok-auth "user:password"
```

The log prints the public URL:

```text
[INFO] ngrok public URL: https://abc123.ngrok-free.app  (basic-auth protected)
```

---

## Multi-Agent Setup

One process owns the Flask dashboard; additional agents attach to it as peers:

```bash
# Primary — runs Flask :5000 + Next.js :3000
python orchestrator.py --workspace ./workspace --workflow sample_workflow

# Satellite — attaches to the running dashboard
python orchestrator.py --workspace ./workspace2 --workflow jobscrap_v2 \
  --server http://localhost:5000 --agent-id worker_1

# Remote satellite over ngrok
python orchestrator.py --workspace ./workspace3 --workflow jobscrap_v2 \
  --server "https://user:password@abc123.ngrok-free.app" --agent-id worker_remote
```

---

## Dashboard Controls

**Dealers panel** (one row per running Card Dealer):

- **Pause / Resume** — freeze or continue card progression
- **Stop** — halt the dealer (keeps history)
- **Deal** — manually advance to the next card
- **Restart** — stop and respawn with the same config

**Agent panel** (AI tmux process):

- **Start** — create tmux session, launch agent, auto-accept consent, paste `AGENT_LOOP.md`
- **Pause** — send Esc (interrupts mid-generation without killing)
- **Stop** — send Ctrl+C × 2, kill session
- **Restart** — send Ctrl+C × 2, relaunch agent in the same session, re-paste loop file
- **Live output** — pane lines streamed in real time via SSE (`/api/agent/stream`)

---

## Workflow Card Format

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

## Completion Tokens

The agent appends to `current_task.md`:

```markdown
## Summary
One sentence summary.

![next]!              # advance to next_card
![next:done]!         # follow the "done" branch
![next:retry]!        # follow the "retry" branch
```

---

## API Reference

### Card Dealer

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/dealers` | List all registered dealers |
| POST | `/api/dealers` | Start new dealer — body: `{workspace, workflow, version}` |
| GET | `/api/dealer/<id>` | Full snapshot for one dealer |
| GET | `/api/dealer/<id>/logs` | Log lines for one dealer |
| GET | `/api/dealer/<id>/history` | Completion history |
| GET | `/api/dealer/<id>/workspace-scan` | Files in this dealer's workspace |
| POST | `/api/dealer/<id>/pause` | Pause dealer |
| POST | `/api/dealer/<id>/resume` | Resume dealer |
| POST | `/api/dealer/<id>/stop` | Stop dealer |
| POST | `/api/dealer/<id>/deal` | Deal next card manually |
| POST | `/api/dealer/<id>/restart` | Stop and respawn dealer |

### AI Agent (tmux)

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/agent` | Session status + last 30 pane lines |
| GET | `/api/agent/stream` | **SSE** — live pane output, one line per event |
| POST | `/api/agent/start` | Start agent (non-blocking) |
| POST | `/api/agent/pause` | Send Esc (pause mid-generation) |
| POST | `/api/agent/stop` | Send Ctrl+C × 2 + kill session |
| POST | `/api/agent/restart` | Interrupt + relaunch in same session (non-blocking) |

### Other

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/status` | Snapshot for `?dealer_id=` (or default) |
| GET | `/api/logs` | Recent log lines |
| GET | `/api/history` | Completed card history |
| GET | `/api/workflows` | Available workflow names and versions |
| GET | `/api/workspace-scan` | Files in the primary workspace |
| GET | `/api/archive` | Recent archive entries |

---

## CLI Flags

| Flag | Short | Default | Description |
| ---- | ----- | ------- | ----------- |
| `--workspace` | `-w` | *(required)* | Directory where `current_task.md` and archive are managed |
| `--workflow` | `-f` | *(required)* | Workflow name (directory under `workflows/`) |
| `--version` | `-v` | `v1` | Workflow version |
| `--workflows-path` | | `./workflows` | Custom path to the workflows root |
| `--port` | `-p` | `5000` | Flask port (ignored in peer-attach mode) |
| `--server` / `--attach` | | — | URL of an existing dashboard to attach to as a peer |
| `--agent-id` | | workspace name | Unique identifier for this agent |
| `--ngrok-auth` | | — | `user:pass` — start a basic-auth-protected ngrok tunnel |
| `--session-name` | | auto | tmux session name |
| `--agent-command` | | `gemini` | AI CLI command to launch in the tmux session |
| `--auto-start` | | false | Auto-start the tmux agent session on launch |

---

## configure_user.json

Drop a `configure_user.json` file at the repo root to store your personal settings (ngrok credentials, workspace paths, agent IDs). This file is gitignored and read by helper scripts — it is **not** loaded automatically by `orchestrator.py`.

```json
{
  "ngrok_auth":   "user:password",
  "workflow":     "sample_workflow",
  "version":      "v1",
  "port":         5000,
  "workspace_1":  "./workspace",
  "workspace_2":  "./workspace2",
  "agent_id_1":   "agent_1",
  "agent_id_2":   "agent_2"
}
```

| Field | Description |
| ----- | ----------- |
| `ngrok_auth` | `user:password` passed to `--ngrok-auth` |
| `workflow` | Default workflow name |
| `version` | Workflow version (e.g. `v1`) |
| `port` | Flask port (default `5000`) |
| `workspace_1` | Path to the primary agent workspace |
| `workspace_2` | Path to the secondary agent workspace |
| `agent_id_1` | ID for the first agent |
| `agent_id_2` | ID for the second agent |

---

## EngineConfig Defaults

`EngineConfig` is the internal Python dataclass wired through all engine components. Its defaults can be changed in `core/config.py`.

| Field | Default | Description |
| ----- | ------- | ----------- |
| `workspace_path` | `./workspace` | Directory where `current_task.md` and archive live |
| `workflows_path` | `./workflows` | Root of workflow definitions |
| `archive_dir` | `archive` | Subdirectory inside workspace for finished tasks |
| `current_task_filename` | `current_task.md` | Name of the active task file the agent writes to |
| `flask_host` | `127.0.0.1` | Bind host for the Flask dashboard |
| `agent_command` | `gemini` | CLI command launched in the tmux session |
| `agent_startup_wait` | `120` | Max seconds to wait for agent prompt before pasting loop file |
