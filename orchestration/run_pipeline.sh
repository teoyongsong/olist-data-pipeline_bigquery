#!/usr/bin/env bash
# BigQuery pipeline wrapper for cron. Usage: ./orchestration/run_pipeline.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ -f .env ]; then set -a; source .env; set +a; fi
mkdir -p logs
exec python orchestration/flow.py >> logs/pipeline.log 2>&1
