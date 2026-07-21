#!/bin/bash
# ScholarFlow — shared helpers for start / stop / restart scripts.
# Source this file from scripts/*.command (not meant to be run alone).

set -euo pipefail

# Resolve repo root from this file's location (scripts/ → parent).
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"

STATE_DIR="${ROOT}/.scholarflow"
PID_BACKEND="${STATE_DIR}/uvicorn.pid"
PID_FRONTEND="${STATE_DIR}/nextjs.pid"
LOG_DIR="${STATE_DIR}/logs"

REQUIRED_MODELS=("qwen3:8b" "deepseek-r1:8b")

# Optional override for CI / constrained hosts: SF_REQUIRED_MODELS=qwen3:8b
if [[ -n "${SF_REQUIRED_MODELS:-}" ]]; then
  IFS=',' read -r -a REQUIRED_MODELS <<< "${SF_REQUIRED_MODELS}"
fi

mkdir -p "${STATE_DIR}" "${LOG_DIR}"

sf_log() {
  echo "[ScholarFlow] $*"
}

sf_err() {
  echo "[ScholarFlow] ERROR: $*" >&2
}

load_env() {
  if [[ -f "${ROOT}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT}/.env"
    set +a
  elif [[ -f "${ROOT}/.env.example" && ! -f "${ROOT}/.env" ]]; then
    sf_log "No .env found — copying .env.example → .env"
    cp "${ROOT}/.env.example" "${ROOT}/.env"
    set -a
    # shellcheck disable=SC1091
    source "${ROOT}/.env"
    set +a
  fi
  API_PORT="${API_PORT:-8000}"
  FRONTEND_PORT="${FRONTEND_PORT:-3000}"
  OLLAMA_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
  OLLAMA_URL="${OLLAMA_URL%/}"
}

port_in_use() {
  local port=$1
  python3 - "${port}" <<'PY'
import glob, sys
port = int(sys.argv[1])
hex_port = f"{port:04X}"
for path in ("/proc/net/tcp", "/proc/net/tcp6"):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            next(fh, None)
            for line in fh:
                parts = line.split()
                if len(parts) < 4:
                    continue
                local, state = parts[1], parts[3]
                if state == "0A" and local.split(":")[-1].upper() == hex_port:
                    sys.exit(0)
    except OSError:
        continue
sys.exit(1)
PY
}

pids_on_port() {
  local port=$1
  python3 - "${port}" <<'PY'
import glob, os, re, sys
port = int(sys.argv[1])
hex_port = f"{port:04X}"
pids = set()

def owners_from_inode(inode: str):
    if not inode or inode == "0":
        return
    for fd in glob.glob("/proc/[0-9]*/fd/[0-9]*"):
        try:
            target = os.readlink(fd)
        except OSError:
            continue
        if f"socket:[{inode}]" in target:
            pid = fd.split("/")[2]
            if pid.isdigit():
                pids.add(pid)

for path in ("/proc/net/tcp", "/proc/net/tcp6"):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            next(fh, None)
            for line in fh:
                parts = line.split()
                if len(parts) < 10:
                    continue
                local = parts[1]
                state = parts[3]
                inode = parts[9]
                if state != "0A":  # LISTEN
                    continue
                if local.split(":")[-1].upper() == hex_port:
                    owners_from_inode(inode)
    except OSError:
        continue

print("\n".join(sorted(pids, key=int)))
PY
}

wait_for_http() {
  local url=$1
  local seconds=${2:-30}
  local i=0
  while (( i < seconds )); do
    if curl -sf "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  return 1
}

ensure_ollama_installed() {
  if command -v ollama >/dev/null 2>&1; then
    sf_log "Ollama CLI found: $(command -v ollama)"
    return 0
  fi
  if [[ "$(uname)" == "Darwin" ]] && [[ -d "/Applications/Ollama.app" ]]; then
    sf_log "Ollama.app found (CLI may be added to PATH after first launch)"
    export PATH="/usr/local/bin:/opt/homebrew/bin:${PATH}"
    if command -v ollama >/dev/null 2>&1; then
      return 0
    fi
    # App exists; open will start the daemon; pull may still need CLI.
    return 0
  fi
  sf_err "Ollama is not installed."
  sf_err "Install from https://ollama.com/download then re-run this script."
  return 1
}

ollama_is_running() {
  curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1
}

ensure_ollama_running() {
  ensure_ollama_installed || return 1

  if ollama_is_running; then
    sf_log "Ollama already running at ${OLLAMA_URL}"
    return 0
  fi

  sf_log "Ollama not running — starting…"
  if [[ "$(uname)" == "Darwin" ]]; then
    open -a Ollama 2>/dev/null || true
    if wait_for_http "${OLLAMA_URL}/api/tags" 20; then
      sf_log "Ollama started via Ollama.app"
      return 0
    fi
  fi

  if command -v ollama >/dev/null 2>&1; then
    nohup ollama serve >>"${LOG_DIR}/ollama.log" 2>&1 &
    echo $! >"${STATE_DIR}/ollama_serve.pid"
    if wait_for_http "${OLLAMA_URL}/api/tags" 25; then
      sf_log "Ollama started (ollama serve)"
      return 0
    fi
  fi

  sf_err "Could not start Ollama at ${OLLAMA_URL}."
  sf_err "Start it manually: ollama serve"
  return 1
}

model_installed() {
  local model=$1
  python3 - "${OLLAMA_URL}" "${model}" <<'PY'
import json, sys, urllib.request
base, wanted = sys.argv[1].rstrip("/"), sys.argv[2].lower()
try:
    with urllib.request.urlopen(base + "/api/tags", timeout=5) as r:
        data = json.load(r)
except Exception:
    sys.exit(1)
for item in data.get("models") or []:
    name = str(item.get("name") or "").lower()
    if name == wanted or name.startswith(wanted + "-") or name.startswith(wanted + ":"):
        sys.exit(0)
sys.exit(1)
PY
}

ensure_required_models() {
  local model
  for model in "${REQUIRED_MODELS[@]}"; do
    if model_installed "${model}"; then
      sf_log "Model present: ${model}"
      continue
    fi
    if ! command -v ollama >/dev/null 2>&1; then
      sf_err "Model ${model} missing and 'ollama' CLI not on PATH — cannot auto-pull."
      return 1
    fi
    sf_log "Pulling missing model: ${model} (this may take a while)…"
    if ! ollama pull "${model}" >>"${LOG_DIR}/ollama-pull.log" 2>&1; then
      sf_err "Failed to pull ${model}. See ${LOG_DIR}/ollama-pull.log"
      return 1
    fi
    sf_log "Pulled: ${model}"
  done
}

ensure_venv() {
  if [[ ! -d "${ROOT}/.venv" ]]; then
    sf_log "Creating Python venv…"
    python3 -m venv "${ROOT}/.venv"
    # shellcheck disable=SC1091
    source "${ROOT}/.venv/bin/activate"
    pip install -q -r "${ROOT}/requirements.txt"
    pip install -q -e "${ROOT}"
  else
    # shellcheck disable=SC1091
    source "${ROOT}/.venv/bin/activate"
  fi
}

ensure_node_modules() {
  if [[ ! -d "${ROOT}/apps/web/node_modules" ]]; then
    sf_log "Installing frontend dependencies (npm install)…"
    (cd "${ROOT}/apps/web" && npm install)
  fi
}

stop_pid_file() {
  local file=$1
  local name=$2
  if [[ ! -f "${file}" ]]; then
    return 0
  fi
  local pid
  pid="$(cat "${file}" 2>/dev/null || true)"
  if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
    sf_log "Stopping ${name} (pid ${pid})"
    # Kill process group if started with setsid / background npm
    kill "${pid}" 2>/dev/null || true
    sleep 0.5
    kill -9 "${pid}" 2>/dev/null || true
  fi
  rm -f "${file}"
}

stop_port_listeners() {
  local port=$1
  local label=$2
  local pids
  pids="$(pids_on_port "${port}")"
  if [[ -z "${pids}" ]]; then
    return 0
  fi
  sf_log "Stopping ${label} listeners on port ${port}: ${pids}"
  # shellcheck disable=SC2086
  kill ${pids} 2>/dev/null || true
  sleep 0.5
  # shellcheck disable=SC2086
  kill -9 ${pids} 2>/dev/null || true
}

stop_scholarflow_services() {
  load_env
  stop_pid_file "${PID_FRONTEND}" "Next.js"
  stop_pid_file "${PID_BACKEND}" "FastAPI"
  stop_port_listeners "${FRONTEND_PORT}" "frontend"
  stop_port_listeners "${API_PORT}" "backend"
  # Never kill Ollama (11434) or ollama_serve.pid intentionally.
  sf_log "ScholarFlow services stopped (Ollama left running)."
}

start_backend() {
  if port_in_use "${API_PORT}"; then
    sf_log "Port ${API_PORT} already in use — reusing existing backend (skip start)."
    return 0
  fi
  sf_log "Starting FastAPI on :${API_PORT}"
  (
    cd "${ROOT}"
    # shellcheck disable=SC1091
    source "${ROOT}/.venv/bin/activate"
    nohup python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port "${API_PORT}" \
      >>"${LOG_DIR}/backend.log" 2>&1 &
    echo $! >"${PID_BACKEND}"
  )
  if wait_for_http "http://127.0.0.1:${API_PORT}/health" 40; then
    sf_log "Backend healthy: http://127.0.0.1:${API_PORT}/health"
  else
    sf_err "Backend did not become healthy. See ${LOG_DIR}/backend.log"
    return 1
  fi
}

start_frontend() {
  if port_in_use "${FRONTEND_PORT}"; then
    sf_log "Port ${FRONTEND_PORT} already in use — reusing existing frontend (skip start)."
    return 0
  fi
  sf_log "Starting Next.js on :${FRONTEND_PORT}"
  (
    cd "${ROOT}/apps/web"
    # Start under a new session so stop can target the whole group via port kill.
    nohup npm run dev -- --hostname 127.0.0.1 --port "${FRONTEND_PORT}" \
      >>"${LOG_DIR}/frontend.log" 2>&1 &
    echo $! >"${PID_FRONTEND}"
  )
  if wait_for_http "http://127.0.0.1:${FRONTEND_PORT}" 90; then
    sf_log "Frontend ready: http://127.0.0.1:${FRONTEND_PORT}"
    # Record the real listener PID when available (npm may spawn a child).
    local listen_pid
    listen_pid="$(pids_on_port "${FRONTEND_PORT}" | awk '{print $1; exit}')"
    if [[ -n "${listen_pid}" ]]; then
      echo "${listen_pid}" >"${PID_FRONTEND}"
    fi
  else
    sf_err "Frontend did not become ready. See ${LOG_DIR}/frontend.log"
    return 1
  fi
}

open_browser() {
  local url="http://localhost:${FRONTEND_PORT}"
  if [[ "$(uname)" == "Darwin" ]]; then
    open "${url}" 2>/dev/null || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${url}" >/dev/null 2>&1 || true
  else
    sf_log "Open ${url} in your browser"
  fi
}

start_scholarflow() {
  load_env
  sf_log "Project root: ${ROOT}"
  sf_log "Logs: ${LOG_DIR}"

  ensure_ollama_running
  ensure_required_models
  ensure_venv
  ensure_node_modules
  start_backend
  start_frontend
  open_browser

  sf_log "Done. Dashboard: http://localhost:${FRONTEND_PORT}"
}
