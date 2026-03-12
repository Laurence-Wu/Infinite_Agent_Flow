#!/usr/bin/env bash
# Usage: ./scripts/start_agent.sh [WORKSPACE] [SESSION_NAME] [AGENT_CMD] [STARTUP_WAIT]
#
# Starts a tmux session, launches the AI agent, waits for it to initialise,
# then pastes AGENT_LOOP.md into the pane.
#
# Defaults:
#   WORKSPACE   = ./workspace
#   SESSION     = gemini_agent
#   AGENT_CMD   = gemini
#   STARTUP_WAIT= 20

set -euo pipefail

WORKSPACE="${1:-./workspace}"
SESSION="${2:-gemini_agent}"
AGENT_CMD="${3:-gemini}"
STARTUP_WAIT="${4:-20}"
LOOP_FILE="${WORKSPACE}/AGENT_LOOP.md"

if [ ! -f "$LOOP_FILE" ]; then
  echo "ERROR: AGENT_LOOP.md not found at $LOOP_FILE" >&2
  exit 1
fi

# Kill existing session with same name if it exists
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Create detached session in the workspace directory
tmux new-session -d -s "$SESSION" -c "$(realpath "$WORKSPACE")"

# Launch the agent
tmux send-keys -t "$SESSION" "$AGENT_CMD" Enter

echo "Session '$SESSION' created — running '$AGENT_CMD'."
echo "Waiting ${STARTUP_WAIT}s for agent to start..."
sleep "$STARTUP_WAIT"

# Check session is still alive
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "ERROR: Session '$SESSION' died during startup." >&2
  exit 1
fi

# Send Ctrl+Y to accept agent consent / "Take control?" prompt
tmux send-keys -t "$SESSION" "C-y" ""
sleep 0.5

# Paste AGENT_LOOP.md content (safe for multi-line markdown)
tmux load-buffer "$(realpath "$LOOP_FILE")"
tmux paste-buffer -t "$SESSION"
tmux send-keys -t "$SESSION" "" Enter

echo "AGENT_LOOP.md pasted. Session '$SESSION' is ready."
echo "Attach with:  tmux attach -t $SESSION"
