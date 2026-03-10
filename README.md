# CardDealer — Agent Instruction Engine

A modular AI agent orchestration system that drives an agent through task workflows
using **card-based instructions**. Each card is a discrete task step written to a
markdown file. The engine monitors the file for a stop token, archives the result,
and deals the next card — creating an **indefinite control loop** for autonomous work.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the sample workflow (infinite loop)
python orchestrator.py --workspace ./output --workflow sample_workflow --version v1

# 3. Open the live dashboard
#    http://localhost:5000
```

## How It Works

```
┌─────────────┐      ┌──────────┐      ┌──────────┐
│   Picker    │─────▶│  Dealer  │─────▶│ Planner  │
│ (load JSON) │      │ (write   │      │ (watch   │
│             │      │  .md)    │      │  .md)    │
└─────────────┘      └──────────┘      └──────────┘
       ▲                                    │
       │         ┌──────────────┐           │
       └─────────│ Orchestrator │◀──────────┘
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │  Dashboard   │
                 │  (Flask)     │
                 └──────────────┘
```

1. **Orchestrator** starts all components and the web dashboard.
2. **Picker** loads the first card from the workflow's JSON chain.
3. **Dealer** wraps the instruction (step-by-step, stop-token footer, metadata)
   and writes `current_task.md` to the workspace.
4. **An AI agent** reads the file, executes the task, and appends `![stop]!`.
5. **Planner** (via watchdog) detects the stop token, extracts the summary,
   archives the file, and tells the Picker to get the next card.
6. The cycle repeats. **If the last card points back to the first, it loops forever.**

## CLI Reference

```
python orchestrator.py [OPTIONS]
```

| Flag | Short | Required | Default | Description |
|------|-------|----------|---------|-------------|
| `--workspace` | `-w` | ✅ | — | Directory where `current_task.md` and `archive/` live |
| `--workflow` | `-f` | ✅ | — | Workflow directory name (under `workflows/`) |
| `--version` | `-v` | No | `v1` | Version subdirectory |
| `--workflows-path` | — | No | `./workflows` | Custom root for all workflows |
| `--port` | `-p` | No | `5000` | Flask dashboard port |

### Examples

```bash
# Run sample workflow on port 8080
python orchestrator.py -w ./output -f sample_workflow -v v1 -p 8080

# Run a custom workflow from another directory
python orchestrator.py -w /data/agent -f my_pipeline -v v2 --workflows-path /opt/workflows
```

## Creating Workflows

A workflow is a directory of versioned JSON cards linked into a chain:

```
workflows/
└── my_workflow/
    └── v1/
        ├── guidance.md          # Optional: high-level guidance for the agent
        ├── card_01.json         # First task
        ├── card_02.json         # Second task
        └── card_03.json         # Third task (next_card → card_01 for loop)
```

### Card JSON Schema

```json
{
  "id": "card_01",
  "workflow": "my_workflow",
  "version": "v1",
  "instruction": "Set up the project structure with src/, tests/, docs/ folders.",
  "metadata": {
    "priority": "high",
    "max_time_seconds": 300,
    "tags": ["setup", "init"]
  },
  "next_card": "card_02"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique card identifier |
| `workflow` | string | ✅ | Parent workflow name |
| `version` | string | ✅ | Workflow version |
| `instruction` | string | ✅ | The task instruction for the agent |
| `metadata.priority` | string | No | `"high"` adds step-by-step guidance |
| `metadata.max_time_seconds` | int | No | Per-card timeout (default: 600s) |
| `metadata.tags` | list | No | Tags for categorization |
| `next_card` | string/null | ✅ | ID of the next card, or the first card's ID for a loop |

### Creating a Circular Loop

Set the **last card's** `next_card` to point back to the **first card**:

```json
// card_01.json
{ "next_card": "card_02" }

// card_02.json (last card)
{ "next_card": "card_01" }   // ← loops back!
```

The agent will work indefinitely: `card_01 → card_02 → card_01 → card_02 → ...`

## Web Dashboard

The live dashboard runs at `http://localhost:<port>` and auto-refreshes via HTMX (no custom JavaScript):

- **Progress bar** — cycles 0-100% per loop iteration, shows cycle count
- **Current Task panel** — card ID, workflow, status badge, instruction preview
- **Available Workflows** — lists all workflows detected in the `workflows/` directory
- **History feed** — reverse-chronological list of completed tasks with summaries

### Dashboard API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Full dashboard page |
| `/api/status` | GET | JSON snapshot of current state |
| `/api/current-task` | GET | Raw markdown of `current_task.md` |
| `/api/workflows` | GET | JSON list of available workflows |
| `/api/history` | GET | JSON list of completed tasks |
| `/partials/status` | GET | HTMX partial: status panel |
| `/partials/progress` | GET | HTMX partial: progress bar |
| `/partials/history` | GET | HTMX partial: history feed |

## Architecture

```
CardDealer/
├── orchestrator.py          # Main entry point + CLI
├── requirements.txt         # flask, watchdog
├── README.md
│
├── core/                    # Shared DRY foundation
│   ├── __init__.py          # Re-exports all core classes
│   ├── base_card.py         # BaseCard (dataclass) + BaseWorkflow
│   ├── config.py            # EngineConfig (paths, timeouts, regex)
│   ├── exceptions.py        # 5 custom exception classes
│   ├── state_manager.py     # Thread-safe StateManager (Lock)
│   └── wrappers.py          # InstructionWrapper (builder pattern)
│
├── engine/                  # Core processing components
│   ├── __init__.py
│   ├── picker.py            # CardsPicker — JSON loader, chain resolver
│   ├── dealer.py            # CardsDealer — markdown writer
│   └── planner.py           # CardsPlanner — watchdog monitor, archiver
│
├── web/                     # Flask dashboard
│   ├── __init__.py
│   ├── app.py               # Flask factory, API + HTMX routes
│   ├── templates/
│   │   ├── index.html       # Main dashboard (Tailwind + HTMX)
│   │   ├── _status.html     # HTMX partial: current task
│   │   ├── _progress.html   # HTMX partial: progress bar
│   │   └── _history.html    # HTMX partial: completed tasks
│   └── static/css/
│       └── style.css        # Glassmorphism, scrollbar, transitions
│
├── workflows/               # Workflow card data
│   └── sample_workflow/
│       └── v1/
│           ├── guidance.md
│           ├── card_01.json
│           └── card_02.json
│
└── tests/                   # Unit tests (49 tests)
    ├── test_core.py         # BaseCard, BaseWorkflow, Wrappers, StateManager
    ├── test_picker.py       # CardsPicker + path traversal security
    ├── test_dealer.py       # CardsDealer markdown output
    └── test_planner.py      # Stop-token regex, archival logic
```

## Workspace Output

When running, the workspace directory will contain:

```
output/
├── current_task.md          # Active task (written by Dealer, read by agent)
├── master_summary.md        # Cumulative summary of all completed tasks
└── archive/
    ├── card_01_20260310_010428.md
    ├── card_02_20260310_010500.md
    └── ...                  # One archived file per completed card
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Configuration

All tunable parameters are in `core/config.py` via the `EngineConfig` dataclass:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `workspace_path` | `"."` | Working directory for task files |
| `workflows_path` | `"./workflows"` | Root directory for workflow data |
| `task_filename` | `"current_task.md"` | Name of the active task file |
| `archive_dirname` | `"archive"` | Name of the archive subdirectory |
| `master_summary_filename` | `"master_summary.md"` | Cumulative summary file |
| `flask_host` | `"127.0.0.1"` | Dashboard bind address |
| `flask_port` | `5000` | Dashboard port |
| `default_timeout_seconds` | `600` | Per-card timeout if not specified in card |
| `stop_token_regex` | `r'!?\[[Ss]top\]!?'` | Forgiving regex for stop-token detection |

## Security

- **Path traversal protection**: All workflow paths are validated using `pathlib.resolve()`.
  Requests like `../../etc/passwd` are blocked by the Picker.
- **Thread safety**: The `StateManager` uses `threading.Lock()` for all reads/writes,
  preventing race conditions between Flask and the Planner.
