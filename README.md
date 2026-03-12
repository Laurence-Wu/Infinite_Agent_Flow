# CardDealer

Card-driven orchestration engine for autonomous AI agent loops. Workflows are sequences of instruction cards; the engine deals tasks, watches for completion signals, archives results, and advances automatically.

---

## What It Does

- Deals structured task cards to an AI agent's workspace (`current_task.md`)
- Watches for the completion token (`![next]!`) and advances the workflow
- Archives every completed card with logs, summary, and metadata
- Supports conditional branching (`![next:label]!`) between cards
- Runs multiple agents in parallel — all visible on one dashboard

---

## Quick Start

```bash
git clone <repo> && cd CardDealer
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Start the engine (owns the dashboard at localhost:3000)
python orchestrator.py --workspace ./workspace --workflow sample_workflow --version v1

# Attach a second agent to the same dashboard
python orchestrator.py --workspace ./workspace2 --workflow jobscrap_v2 --version v1 \
  --server http://localhost:5000 --agent-id agent_1
```

---

## Architecture

```
orchestrator.py
  └─ AgentRegistry
       └─ AgentStack (per agent)
            ├─ CardsPicker   — selects next card from workflow JSON
            ├─ CardsDealer   — writes card instruction to current_task.md
            ├─ CardsPlanner  — watches file, detects ![next]!, advances workflow
            ├─ StateManager  — thread-safe state (local or RemoteStateManager)
            └─ ArchiveManager — saves completed cards to archive/

Flask API (:5000)  ←→  Next.js Dashboard (:3000)
```

**Key directories:**

| Path | Purpose |
| ---- | ------- |
| `workflows/<name>/<version>/` | Read-only card JSON files |
| `workspace/current_task.md` | Active task (writable by agent) |
| `workspace/archive/<loop>/<card>_<ts>/` | Completed task archive |
| `core/` | Base classes, config, state, decorators |
| `engine/` | Picker, dealer, planner, scanner |
| `web/` | Flask routes and app factory |
| `frontend/` | Next.js dashboard |

---

## Workflow Format

Each card is a JSON file:

```json
{
  "id": "card_01",
  "title": "Analyse codebase",
  "instructions": "Scan all Python files and produce a quality report.",
  "next_card": "card_02",
  "branches": {
    "needs_rework": "card_01",
    "approved":     "card_02"
  }
}
```

Cards live at `workflows/<name>/<version>/<id>.json`. They are **never modified** by the engine.

---

## Completion Token

The agent writes to `current_task.md` and ends with a token on its own line:

```
![next]!            # advance to next_card (default)
![next:approved]!   # follow the "approved" branch
![next:needs_rework]!
```

The planner detects the token, archives the card, and deals the next one.

---

## Multi-Agent

The first `orchestrator.py` owns the Flask + Next.js dashboard. Additional agents attach with `--server`:

```bash
python orchestrator.py --workspace ./ws2 --workflow my_flow --version v1 \
  --server http://localhost:5000 --agent-id agent_1
```

All agents appear on the same dashboard. No port conflicts.

---

## API Cheatsheet

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/agents` | List all agents |
| GET | `/api/agent/<id>` | Full snapshot for one agent |
| POST | `/api/agent/<id>/pause` | Pause agent |
| POST | `/api/agent/<id>/resume` | Resume agent |
| POST | `/api/agent/<id>/stop` | Stop agent |
| POST | `/api/agent/<id>/deal` | Force-deal next card |
| POST | `/api/agents` | Start new agent `{workspace, workflow, version}` |
| GET | `/api/status?agent_id=<id>` | Snapshot (backward compat) |
| GET | `/api/archive` | List archive entries |
| GET | `/api/archive/<loop>/<folder>` | Single archive entry |

---

## Configuration

`EngineConfig` fields (all have defaults):

| Field | Default | Description |
| ----- | ------- | ----------- |
| `workspace_path` | `./workspace` | Root dir for task file and archive |
| `workflows_path` | `./workflows` | Root dir for workflow JSON files |
| `archive_dir` | `archive` | Subdirectory name inside workspace |
| `current_task_filename` | `current_task.md` | Active task file name |
| `flask_host` | `127.0.0.1` | Flask bind host |
