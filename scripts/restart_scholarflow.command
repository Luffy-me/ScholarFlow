#!/bin/bash
# Restart ScholarFlow (stop API + UI, then start again). Ollama is left running.

cd "$(dirname "$0")" || exit 1
# shellcheck disable=SC1091
source ./scholarflow_lib.sh

sf_log "=== ScholarFlow restart ==="
stop_scholarflow_services
sleep 1
start_scholarflow
