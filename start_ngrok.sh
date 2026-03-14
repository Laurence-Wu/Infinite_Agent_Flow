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
    # 1. Clean up port 3000 EVERY time the loop restarts
    if lsof -ti :3000 > /dev/null; then
      echo "Port 3000 is in use — cleaning up..."
      lsof -ti :3000 | xargs kill -9 2>/dev/null || true
    fi

    # 2. Aggressive backup to kill invisible Next.js child processes
    # next-server renames itself away from "node" so must be killed separately
    pkill -9 -f node 2>/dev/null || true
    pkill -9 -f next-server 2>/dev/null || true

    # 3. Wait until port 3000 is fully released before starting
    echo "Waiting for port 3000 to be released..."
    for i in $(seq 1 15); do
      lsof -ti :3000 > /dev/null 2>&1 || break
      sleep 1
    done
    if lsof -ti :3000 > /dev/null 2>&1; then
      echo "WARNING: port 3000 still in use after 15s, proceeding anyway..."
    fi

    # 4. Start the orchestrator
    python orchestrator.py \
      --workspace  "${WORKSPACE_1}" \
      --workflow   "${WORKFLOW}" \
      --version    "${VERSION}" \
      --port       "${PORT}" \
      --ngrok-auth "${NGROK_AUTH}" \
      --agent-id   "${AGENT_ID_1}"

    echo "Agent 1 exited — restarting in 10s..."
    sleep 10
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
    echo "Agent 2 exited — restarting in 10s..."
    sleep 10
  done
fi
