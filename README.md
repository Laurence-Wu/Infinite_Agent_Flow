# CardDealer

CardDealer is a card-driven orchestration engine for autonomous agent loops.
It writes one active task markdown file, waits for a completion token, archives
the result, then advances to the next card in a workflow.

This repository currently includes:

- Python orchestration engine (Picker, Dealer, Planner, state + archive)
- Flask API server for control and telemetry
- Next.js dashboard UI (port 3000) proxied to Flask APIs
- Multi-agent support (local registry + peer attach mode)
- Versioned workflows under `workflows/`

## Current Architecture

```text
AgentOrchestrator (orchestrator.py)
  -> build_agent_stack()
     -> EngineConfig
     -> ArchiveManager
     -> StateManager (or RemoteStateManager in attach mode)
     -> CardsPicker
     -> CardsDealer
     -> CardsPlanner (watchdog)

Owner mode only:
  -> Flask app (web/routes.py)
  -> Next.js dev server (frontend/, optional)
  -> ngrok tunnel (optional)
```

Flow per card:

1. Picker loads workflow + current card.
2. Dealer writes `current_task.md` with wrappers and metadata.
3. External agent completes the task and appends `![next]!` or `![next:<label>]!`.
4. Planner detects the token, archives artifacts, updates state, resolves next card.
5. Loop repeats (or finishes if no next card).

## Repository Layout

```text
CardDealer/
  orchestrator.py
  requirements.txt
  README.md
  core/                 # config, state, archive, factory, registry, wrappers
  engine/               # picker, dealer, planner, scanner
  web/                  # Flask app + API routes + legacy templates
  frontend/             # Next.js dashboard UI (app/, components/, lib/)
  workflows/            # versioned workflow cards (JSON + guidance.md)
  workspace/            # runtime output for this repo's local runs
  docs/                 # audits, backlog, sprint/changelog docs
```

## Prerequisites

- Python 3.10+ (recommended)
- Node.js 18+ (required only for Next.js UI)
- `ngrok` in PATH (optional, only if using `--ngrok-auth`)

## Setup

### Python

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### Frontend (optional but recommended)

```bash
cd frontend
npm install
cd ..
```

If `frontend/node_modules` is missing, orchestrator will skip Next.js startup and continue with Flask only.

## Run Modes

### 1) Owner mode (starts Flask, Next.js if available, and planner)

```bash
python orchestrator.py --workspace ./workspace --workflow sample_workflow --version v1
```

UI/API URLs in owner mode:

- Next.js dashboard: `http://localhost:3000`
- Flask API: `http://localhost:5000`

### 2) Peer attach mode (no local Flask)

```bash
python orchestrator.py \
  --workspace ./workspace_peer \
  --workflow sample_workflow \
  --version v1 \
  --server http://localhost:5000 \
  --agent-id agent_1
```

In attach mode, state is reported to the owner server via `/api/report-state`.

### 3) Owner mode with ngrok tunnel (optional)

```bash
python orchestrator.py --workspace ./workspace --workflow jobscrap_v2 --ngrok-auth "user:pass"
```

## CLI Reference

```text
python orchestrator.py [options]
```

| Flag | Short | Required | Default | Notes |
|---|---|---|---|---|
| `--workspace` | `-w` | Yes | - | Directory for `current_task.md` + `archive/` |
| `--workflow` | `-f` | Yes | - | Workflow directory name under `workflows/` |
| `--version` | `-v` | No | `v1` | Workflow version subdirectory |
| `--workflows-path` | - | No | project `workflows/` | Custom workflows root |
| `--port` | `-p` | No | `5000` | Flask port in owner mode |
| `--server` / `--attach` | - | No | `None` | Attach to existing owner dashboard/API |
| `--agent-id` | - | No | derived | Explicit id for this process |
| `--ngrok-auth` | - | No | `None` | Starts ngrok to expose Next.js on port 3000 |

## Workflow Format

Each workflow lives at:

```text
workflows/<workflow_name>/<version>/
  guidance.md      # optional
  *.json           # cards
```

Card schema used by the engine:

```json
{
  "id": "apple",
  "loop_id": "main",
  "workflow": "jobscrap_v2",
  "version": "v1",
  "instruction": "...",
  "metadata": {
    "priority": "high",
    "tags": ["ops", "audit"],
    "custom_wrapper": "optional"
  },
  "branches": {
    "approved": "banana",
    "rework": "cherry"
  },
  "next_card": "banana"
}
```

Notes:

- `branches` is optional. If present, agent can route with `![next:<label>]!`.
- If no branch label is provided, planner uses `next_card`.
- Cards are grouped by `loop_id`. Planner can reshuffle aliases per loop in memory.

## Completion Token Contract

Planner watches `current_task.md` and advances only when token lines are written to disk:

```text
## Summary
<what was done>

![next]!
```

Branch route token variant:

```text
![next:approved]!
```

Important: `![stop]!` is not the planner token in current engine code.
Some older workflow text may still mention `![stop]!`; treat that as legacy wording.

## Runtime Output

Given `--workspace ./workspace`, runtime artifacts include:

```text
workspace/
  current_task.md
  archive/
    <loop_id>/
      <alias>_<timestamp>/
        task.md
        summary.md
        logs.jsonl
        meta.json
    master_summary.md
```

## API Overview (Flask)

Main read endpoints:

- `GET /api/status`
- `GET /api/workflows`
- `GET /api/history`
- `GET /api/current-task`
- `GET /api/logs`
- `GET /api/workspace-scan`
- `GET /api/archive`
- `GET /api/archive/<loop_id>/<folder>`

Agent endpoints:

- `GET /api/agents`
- `POST /api/agents` (start agent)
- `GET /api/agent/<id>`
- `GET /api/agent/<id>/logs`
- `GET /api/agent/<id>/history`
- `POST /api/agent/<id>/pause`
- `POST /api/agent/<id>/resume`
- `POST /api/agent/<id>/stop`
- `POST /api/agent/<id>/deal`
- `POST /api/report-state` (peer state ingestion)

Backward-compatible aliases are also exposed under `/api/workflow/*`, `/api/deal-next`, `/api/agent/start`.

## Frontend Notes

- Next.js dev server runs on port `3000`.
- `frontend/next.config.js` rewrites `/api/*` to Flask on `localhost:${FLASK_PORT}`.
- Orchestrator sets `FLASK_PORT` when launching frontend in owner mode.

## Workflows Present In This Repo

- `sample_workflow/v1`
- `cardDealer_evolve/v1`
- `jobscrap_v2/v1`

## Troubleshooting

### Frontend did not start

Cause: missing `frontend/node_modules` or missing `npm`.

Fix:

```bash
cd frontend
npm install
```

### No workflow advancement

Cause: completion token not written exactly as expected.

Fix: ensure `current_task.md` contains `![next]!` or `![next:<label>]!` on its own line.

### Attach mode agent not visible

Cause: owner server URL unreachable or wrong port.

Fix: verify owner mode is running and reachable at the `--server` URL.

## Security Notes

- Never commit secrets (`.env`, private keys, credential files).
- Treat `--ngrok-auth user:pass` as sensitive and rotate if exposed.
- Workflow path resolution is guarded against directory traversal in picker.
