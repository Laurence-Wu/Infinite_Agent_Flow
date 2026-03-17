# CardDealer

**Card-driven orchestration engine for autonomous AI agent loops**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-black.svg)](https://nextjs.org)

Built by [Laurence Wu](https://github.com/Laurence-Wu)

---

![CardDealer Dashboard](docs/dashboard.png)

*Live dashboard — three concurrent agents running independent workflow loops with real-time cycle counts and uptime.*

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

## Image Generation Prompts

Prompts for generating architecture diagrams:

### System Architecture

> Minimalist dark-theme technical diagram of an AI orchestration system. Left: a stack of JSON cards labeled "Workflow Cards". Center: a box labeled "Card Dealer Engine" with glowing amber arrows. Right: a terminal labeled "AI Agent (tmux)" with streaming green text. Below: a file icon labeled "current_task.md". A dashed loop arrow returns from agent to engine labeled "stop token → next card". Charcoal background, amber and teal accents, clean sans-serif labels.

### Multi-Agent Dashboard

> Dark UI illustration of a monitoring dashboard with three autonomous agent cards in a grid. Each card shows: agent name, amber "Running" status pill, cycle counter, done counter, uptime clock. Left sidebar: Dashboard, Workflows, Files, History, Logs, Settings. Near-black background (#1a1a1a), amber (#f5a623) highlights, white monospace text. Flat design.

### Infinite Improvement Loop

> Abstract dark-background flowchart of a perpetual improvement cycle. Outer ring of 8 nodes: Scaffold → Events → Hooks → Adapters → V2 Adapters → Server → Frontend → Integration. Inner ring of 5 nodes: DRY Audit → Test Suite → Profiling → Hardening → Analysis, looping back to DRY Audit. Amber arrows, circuit-board aesthetic, title "CardDealer Workflow Loop".

### Card-to-Agent Pipeline

> Horizontal pipeline infographic, 5 stages with right-pointing arrows. Stage 1: JSON card icon "Card Loaded". Stage 2: text file icon "Instruction Written". Stage 3: terminal icon "Agent Executes". Stage 4: checkmark document "Stop Token Detected". Stage 5: branching arrow "Next Card / Branch". Dark background, amber nodes, white labels.

---

## License

MIT © [Laurence Wu](https://github.com/Laurence-Wu)
