# CardDealer

**Card-driven orchestration engine for autonomous AI agent loops**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-black.svg)](https://nextjs.org)

Built by [Laurence Wu](https://github.com/Laurence-Wu)

---

![CardDealer Dashboard](docs/screenshot_dashboard.png)

*Live dashboard — three concurrent agents (fast_dllm, job_war_room, game_farmers) running independent workflow loops with real-time cycle counts and uptime.*

---

## How It Works

| Workflow Loop | Multi-Agent Network |
| :---: | :---: |
| ![Workflow Loop Diagram](docs/diagram_workflow_loop.jpg) | ![Multi-Agent Diagram](docs/diagram_multi_agent.jpg) |
| *CardDealer Engine cycles through cards indefinitely* | *Multiple agents share one dashboard via SSE streaming* |

| Workflows Page |
| :---: |
| ![Workflows Page](docs/screenshot_workflows.png) |
| *All registered workflows listed with version and card counts* |

---

## Overview

CardDealer drives AI agents through structured, repeating task sequences defined as JSON cards. Each card contains an instruction; the engine writes it to disk, waits for the agent to complete and append a stop token, then advances to the next card — or follows a conditional branch. Loops run indefinitely, making it suitable for continuous improvement pipelines, automated research cycles, and multi-agent coordination.

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  JSON Cards │────▶│  Card Dealer │────▶│  AI Agent (tmux)│────▶│current_task  │
│ workflows/  │     │ tracks state │     │ Gemini / Claude  │     │    .md       │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────┬───────┘
        ▲                   │                                            │
        │                   └──────────────── stop token ◀──────────────┘
        │                                    ![next]!
        └────────────────────── next card ───┘
```

### Key Features

- **Workflow loops** — cards cycle indefinitely or branch conditionally on agent output
- **Multi-agent** — run N agents against one shared dashboard; each owns its workspace
- **Live dashboard** — Next.js UI with real-time SSE streaming, cycle counters, log terminal
- **Remote access** — optional ngrok tunnel with HTTP basic-auth
- **Archive** — every completed card is saved with its summary and metadata

---

## Installation

**Prerequisites:** Python 3.10+, Node.js 18+, tmux (Linux/macOS/WSL)

```bash
git clone https://github.com/Laurence-Wu/Infinite_Agent_Flow.git
cd CardDealer
pip install -r requirements.txt
cd frontend && npm install && cd ..
cp configure_user.sample.json configure_user.json
# edit configure_user.json with your settings
```

---

## Quick Start

```bash
# Linux / macOS / WSL
bash scripts/start.sh        # primary agent
bash scripts/start.sh 2      # second agent on same dashboard

# Windows
scripts\start.bat
```

Or launch directly:

```bash
python orchestrator.py \
  --workspace ./workspace \
  --workflow  sample_workflow \
  --version   v1 \
  --agent-id  my_agent \
  --auto-start
```

Dashboard: `http://localhost:3000`

---

## Multi-Agent Setup

One process owns the Flask server; additional agents attach as peers:

```bash
# Primary — starts Flask :5000 + Next.js :3000
python orchestrator.py \
  --workspace ./workspace \
  --workflow  sample_workflow

# Satellite — attaches to existing dashboard
python orchestrator.py \
  --workspace ./workspace2 \
  --workflow  jobscrap_v2 \
  --server    http://localhost:5000 \
  --agent-id  worker_2

# Remote satellite over ngrok
python orchestrator.py \
  --workspace ./workspace3 \
  --workflow  jobscrap_v2 \
  --server    "https://user:pass@abc123.ngrok-free.app" \
  --agent-id  worker_remote
```

---

## Workflow Card Format

Cards are static JSON files at `workflows/<name>/<version>/<id>.json`. The engine never modifies them.

```json
{
  "id":        "card_01",
  "title":     "Scaffold shared utilities",
  "instruction": "Create llada/api/constants.py with DEFAULT_PORT = 5050 ...",
  "next_card": "card_02",
  "loop_id":   "build",
  "priority":  "high",
  "branches": {
    "exists": "card_02",
    "retry":  "card_01"
  }
}
```

| Field | Required | Description |
| ----- | -------- | ----------- |
| `id` | ✓ | Unique card identifier |
| `instruction` | ✓ | Full task text delivered to the agent |
| `next_card` | ✓ | Default next card |
| `loop_id` | — | Groups cards into a named loop |
| `branches` | — | Conditional routing by stop-token label |
| `priority` | — | `high` adds step-by-step scaffolding |

---

## Stop Tokens

The agent appends to `current_task.md` when the task is complete:

```markdown
## Summary
- **Files changed**: core/archive.py
- **Commands run**: python -m pytest tests/ -q
- **Tests**: 42 passed
- **Git**: abc1234

![next]!              ← advance to next_card
![next:done]!         ← follow the "done" branch
![next:retry]!        ← follow the "retry" branch
```

The engine watches `current_task.md` for the stop token, extracts the summary, archives the result, then deals the next card.

---

## Remote Access via ngrok

```bash
# Authenticate ngrok once
ngrok config add-authtoken <your-token>

# Start with a public tunnel
python orchestrator.py \
  --workspace ./workspace \
  --workflow  sample_workflow \
  --ngrok-auth "user:password"
```

```text
[INFO] ngrok public URL: https://abc123.ngrok-free.app  (basic-auth protected)
```

---

## CLI Reference

| Flag | Default | Description |
| ---- | ------- | ----------- |
| `--workspace` | *(required)* | Directory where `current_task.md` lives |
| `--workflow` | *(required)* | Workflow name under `workflows/` |
| `--version` | `v1` | Workflow version |
| `--port` | `5000` | Flask port |
| `--server` / `--attach` | — | Attach to an existing dashboard as a peer |
| `--agent-id` | workspace name | Unique agent identifier |
| `--ngrok-auth` | — | `user:pass` — start a basic-auth-protected ngrok tunnel |
| `--agent-command` | `gemini` | AI CLI command launched in the tmux session |
| `--auto-start` | `false` | Auto-launch the tmux agent session on startup |

---

## REST API

### Dealer

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET` | `/api/dealers` | List all registered dealers |
| `POST` | `/api/dealers` | Start a new dealer |
| `GET` | `/api/dealer/<id>` | Full state snapshot |
| `GET` | `/api/dealer/<id>/logs` | Recent log lines |
| `GET` | `/api/dealer/<id>/history` | Completed card history |
| `POST` | `/api/dealer/<id>/pause` | Pause card progression |
| `POST` | `/api/dealer/<id>/resume` | Resume card progression |
| `POST` | `/api/dealer/<id>/stop` | Stop the dealer |
| `POST` | `/api/dealer/<id>/deal` | Manually advance to next card |
| `POST` | `/api/dealer/<id>/restart` | Stop and respawn |

### Agent

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET` | `/api/agent` | Session status + last 30 pane lines |
| `GET` | `/api/agent/stream` | **SSE** — live tmux pane output |
| `POST` | `/api/agent/start` | Start agent session |
| `POST` | `/api/agent/pause` | Send Esc (interrupt mid-generation) |
| `POST` | `/api/agent/stop` | Send Ctrl+C × 2 + kill session |
| `POST` | `/api/agent/restart` | Interrupt and relaunch in same session |

---

## License

MIT © [Laurence Wu](https://github.com/Laurence-Wu)
