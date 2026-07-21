#!/bin/bash
# Stop FastAPI + Next.js. Does NOT stop Ollama.

cd "$(dirname "$0")" || exit 1
# shellcheck disable=SC1091
source ./scholarflow_lib.sh

stop_scholarflow_services
