#!/bin/bash
# Start ScholarFlow with one click (macOS: double-click this file).
# Terminal: ./scripts/start_scholarflow.command

cd "$(dirname "$0")" || exit 1
# shellcheck disable=SC1091
source ./scholarflow_lib.sh

start_scholarflow
