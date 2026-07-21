#!/bin/bash
# Stops ScholarFlow API + Next.js (keeps Ollama running).
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck disable=SC1091
source ./scholarflow_lib.sh

stop_pid_file() {
  local file=$1
  local name=$2
  if [[ -f "$file" ]]; then
    local pid
    pid=$(cat "$file")
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $name (pid $pid)"
      kill "$pid" 2>/dev/null || true
    fi
    rm -f "$file"
  fi
}

stop_pid_file "$PID_FRONTEND" "Next.js"
stop_pid_file "$PID_BACKEND" "FastAPI"

# Fallback: processes bound to default ports
if command -v lsof >/dev/null 2>&1; then
  for port in "$FRONTEND_PORT" "$API_PORT"; do
    pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
      echo "Stopping listeners on port $port"
      kill $pids 2>/dev/null || true
    fi
  done
fi

echo "ScholarFlow stopped (Ollama left running)."
