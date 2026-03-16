# CardDealer

Card-driven orchestration engine for autonomous AI agent loops.

> Built by [Laurence Wu](https://github.com/Laurence-Wu)

---

![CardDealer Dashboard](docs/dashboard.png)

*Live dashboard showing three concurrent agents — fast_dllm, job_war_room, and game_farmers — each running independent workflow loops with real-time cycle counts and uptime.*

---

## How It Works

```text
Workflow Cards  →  Card Dealer  →  AI Agent (tmux)  →  current_task.md  →  Stop Token  →  next Card
     │                  │                │                     │                 │
  JSON files       tracks state     Gemini/Claude        agent writes        ![next]!
  in workflows/    advances loop    in tmux pane         its output          ![next:branch]!
```

**Card Dealer** reads a JSON card, writes its instruction to `current_task.md`, waits for the AI agent to append a stop token, then advances to the next card (or follows a branch). Loops run indefinitely unless stopped.

---

## Install

```bash
git clone <repo> && cd CardDealer
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

Copy `configure_user.sample.json` → `configure_user.json` and fill in your settings.

---

## Quick Start

```bash
# Linux / macOS / WSL
bash scripts/start.sh        # primary agent
bash scripts/start.sh 2      # second agent on same dashboard

# Windows
scripts\start.bat
scripts\start.bat 2
```

Or launch directly:

```bash
python orchestrator.py \
  --workspace ./workspace \
  --workflow sample_workflow \
  --version v1 \
  --agent-id my_agent \
  --auto-start
```

Dashboard opens at `http://localhost:3000`.

---

## Multi-Agent

```bash
# Primary — owns the Flask server and Next.js dashboard
python orchestrator.py --workspace ./workspace --workflow sample_workflow

# Satellite — attaches to the running dashboard as a peer
python orchestrator.py --workspace ./workspace2 --workflow jobscrap_v2 \
  --server http://localhost:5000 --agent-id worker_2
```

---

## Workflow Card Format

```json
{
  "id": "card_01",
  "title": "Task title",
  "instruction": "What the agent must do.",
  "next_card": "card_02",
  "loop_id": "improve",
  "branches": {
    "retry": "card_01",
    "done":  "card_02"
  }
}
```

Cards live at `workflows/<name>/<version>/<id>.json` — never modified by the engine.

---

## Stop Tokens

The agent appends to `current_task.md` to signal completion:

```markdown
![next]!              # advance to next_card
![next:done]!         # follow the "done" branch
![next:retry]!        # follow the "retry" branch
```

---

## ngrok (Remote Access)

```bash
ngrok config add-authtoken <your-token>

python orchestrator.py --workspace ./workspace --workflow sample_workflow \
  --ngrok-auth "user:password"
```

Prints: `ngrok public URL: https://abc123.ngrok-free.app  (basic-auth protected)`

---

## CLI Flags

| Flag | Default | Description |
| ---- | ------- | ----------- |
| `--workspace` | *(required)* | Directory where `current_task.md` lives |
| `--workflow` | *(required)* | Workflow name under `workflows/` |
| `--version` | `v1` | Workflow version |
| `--port` | `5000` | Flask port |
| `--server` / `--attach` | — | Attach to an existing dashboard as a peer |
| `--agent-id` | workspace name | Unique agent identifier |
| `--ngrok-auth` | — | `user:pass` for a public ngrok tunnel |
| `--agent-command` | `gemini` | AI CLI command launched in tmux |
| `--auto-start` | false | Auto-start tmux agent on launch |

---

## API

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/dealers` | List all dealers |
| POST | `/api/dealers` | Start a new dealer |
| GET | `/api/dealer/<id>` | Dealer snapshot |
| POST | `/api/dealer/<id>/pause` | Pause |
| POST | `/api/dealer/<id>/resume` | Resume |
| POST | `/api/dealer/<id>/stop` | Stop |
| POST | `/api/dealer/<id>/deal` | Manually advance card |
| POST | `/api/dealer/<id>/restart` | Restart |
| GET | `/api/agent/stream` | SSE — live tmux pane output |
| POST | `/api/agent/start` | Start agent session |
| POST | `/api/agent/stop` | Stop agent session |
| POST | `/api/agent/restart` | Restart agent session |

---

## Image Generation Prompts

Use these prompts to generate workflow diagrams for CardDealer:

### System Architecture

> "Minimalist dark-theme technical diagram of an AI orchestration system. Left side: a stack of JSON cards labeled 'Workflow Cards'. Center: a black box labeled 'Card Dealer Engine' with glowing amber arrows flowing through it. Right side: a terminal window labeled 'AI Agent (tmux)' with streaming green text. Below the engine: a file icon labeled 'current_task.md'. A dashed loop arrow connects the agent back to the engine labeled 'stop token → next card'. Clean sans-serif labels, deep charcoal background, amber and teal accent colors."

### Multi-Agent Dashboard

> "Dark UI dashboard screenshot-style illustration showing three autonomous AI agent cards in a grid layout. Each card has a name badge, a status pill labeled 'Running' in amber, cycle counter, task-done counter, and uptime clock. Top navigation sidebar lists: Dashboard, Workflows, Files, History, Logs, Settings. The color palette is near-black background (#1a1a1a), amber (#f5a623) highlights, and white text. Flat design, no shadows, monospace font."

### Infinite Loop Flow

> "Abstract flowchart on a dark background showing a perpetual improvement cycle. Eight rectangular nodes in a clockwise ring labeled: Scaffold → Events → Hooks → Adapters → V2 Adapters → Server → Frontend → Integration. Five more nodes in an inner ring labeled: DRY Audit → Test Suite → Profiling → Hardening → Analysis. Glowing amber arrows connect outer ring sequentially; inner ring arrows loop back to DRY Audit. Title: 'CardDealer Workflow Loop'. Futuristic, circuit-board aesthetic."

### Card-to-Agent Pipeline

> "Infographic showing a horizontal pipeline with five stages connected by right-pointing arrows. Stage 1: a JSON card icon labeled 'Card Loaded'. Stage 2: a text file icon labeled 'Instruction Written'. Stage 3: a robot/terminal icon labeled 'Agent Executes'. Stage 4: a checkmark document labeled 'Stop Token Detected'. Stage 5: a branching arrow labeled 'Next Card / Branch'. Dark background, amber nodes, white labels, flat icon style."

---

## License

MIT
