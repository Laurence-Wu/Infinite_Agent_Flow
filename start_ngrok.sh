#!/usr/bin/env bash
# start_ngrok.sh — Launch all 3 CardDealer agents with ngrok and auto-restart.
# Agent 1 (fast_dllm):   gemini  @ Fast-dllm       — primary server + ngrok
# Agent 2 (job_war_room): gemini  @ Job-war-room    — attached
# Agent 3 (game_farmers): qwen    @ GameFarmerJS    — attached

set -euo pipefail

CONFIG="$(cd "$(dirname "$0")" && pwd)/configure_user.json"

if [ ! -f "$CONFIG" ]; then
  echo "ERROR: $CONFIG not found."
  echo "Copy configure_user.sample.json → configure_user.json and fill in your credentials."
  exit 1
fi

read_cfg() { python3 -c "import json; d=json.load(open('$CONFIG')); print(d.get('$1',''))" ; }

NGROK_AUTH="$(read_cfg ngrok_auth)"
VERSION="$(read_cfg version)"
PORT="$(read_cfg port)"

WORKSPACE_1="$(read_cfg workspace_1)"; WORKFLOW_1="$(read_cfg workflow_1)"; AGENT_ID_1="$(read_cfg agent_id_1)"; AGENT_CMD_1="$(read_cfg agent_command_1)"
WORKSPACE_2="$(read_cfg workspace_2)"; WORKFLOW_2="$(read_cfg workflow_2)"; AGENT_ID_2="$(read_cfg agent_id_2)"; AGENT_CMD_2="$(read_cfg agent_command_2)"
WORKSPACE_3="$(read_cfg workspace_3)"; WORKFLOW_3="$(read_cfg workflow_3)"; AGENT_ID_3="$(read_cfg agent_id_3)"; AGENT_CMD_3="$(read_cfg agent_command_3)"

echo "=== Infinite Agent Flow — 3-agent launch ==="
echo "  Agent 1: ${AGENT_ID_1} | ${WORKFLOW_1}/${VERSION} | cmd=${AGENT_CMD_1:-default}"
echo "  Agent 2: ${AGENT_ID_2} | ${WORKFLOW_2}/${VERSION} | cmd=${AGENT_CMD_2:-default}"
echo "  Agent 3: ${AGENT_ID_3} | ${WORKFLOW_3}/${VERSION} | cmd=${AGENT_CMD_3:-default}"
echo ""

# ── Kill all child processes on Ctrl+C / exit ─────────────────────────────────
trap 'echo ""; echo "Shutting down all agents..."; kill 0 2>/dev/null; exit 0' EXIT INT TERM

# ── Port 3000 cleanup ─────────────────────────────────────────────────────────
cleanup_port_3000() {
  if lsof -ti :3000 > /dev/null 2>&1; then
    echo "[boot] Port 3000 in use — killing..."
    lsof -ti :3000 | xargs kill -9 2>/dev/null || true
  fi
  pkill -9 -f next-server 2>/dev/null || true
  pkill -9 -f "next dev"  2>/dev/null || true
  echo "[boot] Waiting for port 3000..."
  for i in $(seq 1 15); do
    lsof -ti :3000 > /dev/null 2>&1 || break
    sleep 1
  done
}

# ── Wait for Flask API ────────────────────────────────────────────────────────
wait_for_server() {
  echo "[boot] Waiting for Flask server on port ${PORT}..."
  for i in $(seq 1 30); do
    curl -s --max-time 1 "http://localhost:${PORT}/api/dealers" > /dev/null 2>&1 && \
      echo "[boot] Server ready." && return 0
    sleep 2
  done
  echo "[boot] WARNING: server did not respond after 60s — starting attached agents anyway."
}

# ── Agent 1: primary (server + ngrok) ────────────────────────────────────────
cleanup_port_3000
(
  while true; do
    echo "[Agent 1 / ${AGENT_ID_1}] Starting — gemini @ ${WORKSPACE_1}"
    ARGS=(
      python3 orchestrator.py
      --workspace  "${WORKSPACE_1}"
      --workflow   "${WORKFLOW_1}"
      --version    "${VERSION}"
      --port       "${PORT}"
      --agent-id   "${AGENT_ID_1}"
      --auto-start
    )
    [ -n "${NGROK_AUTH}" ]  && ARGS+=(--ngrok-auth    "${NGROK_AUTH}")
    [ -n "${AGENT_CMD_1}" ] && ARGS+=(--agent-command "${AGENT_CMD_1}")
    "${ARGS[@]}" || true
    echo "[Agent 1 / ${AGENT_ID_1}] Exited — restarting in 10s..."
    sleep 10
  done
) &

wait_for_server

# ── Agent 2: attached ─────────────────────────────────────────────────────────
(
  while true; do
    echo "[Agent 2 / ${AGENT_ID_2}] Starting — gemini @ ${WORKSPACE_2}"
    ARGS=(
      python3 orchestrator.py
      --workspace "${WORKSPACE_2}"
      --workflow  "${WORKFLOW_2}"
      --version   "${VERSION}"
      --attach    "http://localhost:${PORT}"
      --agent-id  "${AGENT_ID_2}"
      --auto-start
    )
    [ -n "${AGENT_CMD_2}" ] && ARGS+=(--agent-command "${AGENT_CMD_2}")
    "${ARGS[@]}" || true
    echo "[Agent 2 / ${AGENT_ID_2}] Exited — restarting in 10s..."
    sleep 10
  done
) &

# ── Agent 3: attached ─────────────────────────────────────────────────────────
(
  while true; do
    echo "[Agent 3 / ${AGENT_ID_3}] Starting — qwen @ ${WORKSPACE_3}"
    ARGS=(
      python3 orchestrator.py
      --workspace "${WORKSPACE_3}"
      --workflow  "${WORKFLOW_3}"
      --version   "${VERSION}"
      --attach    "http://localhost:${PORT}"
      --agent-id  "${AGENT_ID_3}"
      --auto-start
    )
    [ -n "${AGENT_CMD_3}" ] && ARGS+=(--agent-command "${AGENT_CMD_3}")
    "${ARGS[@]}" || true
    echo "[Agent 3 / ${AGENT_ID_3}] Exited — restarting in 10s..."
    sleep 10
  done
) &

echo "[boot] All 3 agents running. Press Ctrl+C to stop everything."
wait
