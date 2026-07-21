#!/bin/bash
# ScholarFlow — shared helpers for start/stop scripts
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT/.scholarflow"
PID_BACKEND="$STATE_DIR/uvicorn.pid"
PID_FRONTEND="$STATE_DIR/nextjs.pid"
LOG_DIR="$STATE_DIR/logs"

mkdir -p "$STATE_DIR" "$LOG_DIR"

load_env() {
  if [[ -f "$ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT/.env"
    set +a
  fi
}

API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"

ensure_venv() {
  if [[ ! -d "$ROOT/.venv" ]]; then
    echo "Creating Python venv..."
    python3 -m venv "$ROOT/.venv"
    # shellcheck disable=SC1091
    source "$ROOT/.venv/bin/activate"
    pip install -r "$ROOT/requirements.txt"
    pip install -e "$ROOT"
  else
    # shellcheck disable=SC1091
    source "$ROOT/.venv/bin/activate"
  fi
}

ensure_ollama() {
  if curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    echo "Ollama already running at $OLLAMA_URL"
    return 0
  fi
  echo "Starting Ollama..."
  if [[ "$(uname)" == "Darwin" ]]; then
    open -a Ollama 2>/dev/null || true
    sleep 2
  fi
  if ! curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    nohup ollama serve >>"$LOG_DIR/ollama.log" 2>&1 &
    sleep 2
  fi
}

port_in_use() {
  local port=$1
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1
  else
    return 1
  fi
}
