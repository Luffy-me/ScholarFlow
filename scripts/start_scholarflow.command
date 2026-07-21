#!/bin/bash
# Double-click on macOS (or run from terminal) to start ScholarFlow.
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck disable=SC1091
source ./scholarflow_lib.sh
load_env

echo "=== ScholarFlow start ==="
ensure_ollama
ensure_venv

if port_in_use "$API_PORT"; then
  echo "Port $API_PORT already in use — skipping backend start (or run stop_scholarflow.command)"
else
  echo "Starting FastAPI on :$API_PORT"
  (cd "$ROOT" && nohup python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port "$API_PORT" \
    >>"$LOG_DIR/backend.log" 2>&1 & echo $! >"$PID_BACKEND")
fi

if [[ ! -d "$ROOT/apps/web/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$ROOT/apps/web" && npm install)
fi

if port_in_use "$FRONTEND_PORT"; then
  echo "Port $FRONTEND_PORT already in use — skipping frontend start"
else
  echo "Starting Next.js on :$FRONTEND_PORT"
  (cd "$ROOT/apps/web" && nohup npm run dev -- --port "$FRONTEND_PORT" >>"$LOG_DIR/frontend.log" 2>&1 &)
  echo $! >"$PID_FRONTEND"
fi

sleep 2
if [[ "$(uname)" == "Darwin" ]]; then
  open "http://127.0.0.1:${FRONTEND_PORT}"
else
  echo "Open http://127.0.0.1:${FRONTEND_PORT} in your browser"
fi

echo "Logs: $LOG_DIR"
echo "Done."
