#!/usr/bin/env bash
# start_ngrok.sh — Launch CardDealer with ngrok and auto-restart.
# Reads credentials and config from configure_user.json (gitignored).
# If no primary agent is running → start Agent 1 (server + ngrok).
# If Agent 1 is already up      → start Agent 2 (attached, no server).

CONFIG="$(dirname "$0")/configure_user.json"

if [ ! -f "$CONFIG" ]; then
  echo "ERROR: $CONFIG not found."
  echo "Copy configure_user.sample.json → configure_user.json and fill in your credentials."
  exit 1
fi

# Parse JSON with python (no jq dependency needed)
read_cfg() { python -c "import json,sys; d=json.load(open('$CONFIG')); print(d.get('$1',''))" ; }

NGROK_AUTH="$(read_cfg ngrok_auth)"
WORKFLOW="$(read_cfg workflow)"
VERSION="$(read_cfg version)"
PORT="$(read_cfg port)"
WORKSPACE_1="$(read_cfg workspace_1)"
WORKSPACE_2="$(read_cfg workspace_2)"
AGENT_ID_1="$(read_cfg agent_id_1)"
AGENT_ID_2="$(read_cfg agent_id_2)"

# Check whether Agent 1's Flask server is already listening on $PORT
if ! curl -s --max-time 2 "http://localhost:${PORT}/api/agents" > /dev/null 2>&1; then
  echo "No primary agent detected on port ${PORT} — starting Agent 1 (server + ngrok)..."
  while true; do
    python orchestrator.py \
      --workspace  "${WORKSPACE_1}" \
      --workflow   "${WORKFLOW}" \
      --version    "${VERSION}" \
      --port       "${PORT}" \
      --ngrok-auth "${NGROK_AUTH}" \
      --agent-id   "${AGENT_ID_1}"
    echo "Agent 1 exited — restarting in 3s..."
    sleep 3
  done
else
  echo "Agent 1 already running on port ${PORT} — starting Agent 2 (attached)..."
  while true; do
    python orchestrator.py \
      --workspace "${WORKSPACE_2}" \
      --workflow  "${WORKFLOW}" \
      --version   "${VERSION}" \
      --attach    "http://localhost:${PORT}" \
      --agent-id  "${AGENT_ID_2}"
    echo "Agent 2 exited — restarting in 3s..."
    sleep 3
  done
fi
