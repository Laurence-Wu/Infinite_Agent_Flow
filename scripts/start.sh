#!/usr/bin/env bash
# Usage: bash scripts/start.sh [1|2]
# Reads configure_user.json and launches orchestrator.py with ngrok, workspace,
# workflow, port, and auto-start. Pass 2 to use workspace_2 / agent_id_2.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT_DIR/configure_user.json"

get() { python3 -c "import json; d=json.load(open('$CONFIG')); print(d.get('$1',''))" 2>/dev/null || echo ""; }

N="${1:-1}"

NGROK_AUTH="$(get ngrok_auth)"
WORKFLOW="$(get workflow)";    [ -z "$WORKFLOW"  ] && WORKFLOW="sample_workflow"
VERSION="$(get version)";      [ -z "$VERSION"   ] && VERSION="v1"
PORT="$(get port)";            [ -z "$PORT"      ] && PORT="5000"
WORKSPACE="$(get "workspace_${N}")"; [ -z "$WORKSPACE" ] && WORKSPACE="./workspace"
AGENT_ID="$(get "agent_id_${N}")";   [ -z "$AGENT_ID"  ] && AGENT_ID="agent_${N}"

ARGS=(
  python3 "$ROOT_DIR/orchestrator.py"
  --workspace "$WORKSPACE"
  --workflow  "$WORKFLOW"
  --version   "$VERSION"
  --port      "$PORT"
  --agent-id  "$AGENT_ID"
  --auto-start
)

[ -n "$NGROK_AUTH" ] && ARGS+=(--ngrok-auth "$NGROK_AUTH")

echo "workspace : $WORKSPACE"
echo "workflow  : $WORKFLOW/$VERSION"
echo "agent-id  : $AGENT_ID"
echo "port      : $PORT"
echo "ngrok     : ${NGROK_AUTH:+enabled}${NGROK_AUTH:-disabled}"
echo ""

exec "${ARGS[@]}"
