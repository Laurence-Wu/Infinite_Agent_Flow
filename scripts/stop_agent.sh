#!/usr/bin/env bash
# Usage: ./scripts/stop_agent.sh [SESSION_NAME]
#
# Sends Ctrl-C three times to interrupt the agent, then kills the tmux session.

SESSION="${1:-gemini_agent}"

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Session '$SESSION' is not running."
  exit 0
fi

echo "Interrupting agent in '$SESSION'..."
for i in 1 2 3; do
  tmux send-keys -t "$SESSION" "C-c" "" 2>/dev/null || true
  sleep 0.3
done

sleep 1
tmux kill-session -t "$SESSION" 2>/dev/null || true
echo "Session '$SESSION' stopped."
