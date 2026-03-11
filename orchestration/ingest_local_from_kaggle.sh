#!/usr/bin/env bash
# Download Olist dataset from Kaggle and ingest directly from local CSVs into BigQuery.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Load environment variables from .env if present
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . .env
  set +a
fi

DATA_DIR="${DATA_DIR:-$ROOT/data/olist}"

if ! command -v kaggle >/dev/null 2>&1; then
  echo "kaggle CLI not found."
  echo "Install it with: pip install kaggle"
  echo "Then configure your Kaggle API token (KAGGLE_USERNAME / KAGGLE_KEY)."
  exit 1
fi

echo "Downloading Olist dataset from Kaggle into ${DATA_DIR} ..."
mkdir -p "${DATA_DIR}"
kaggle datasets download -d olistbr/brazilian-ecommerce -p "${DATA_DIR}" --unzip --force

echo "Ingesting local CSVs into BigQuery (raw_olist) ..."
python ingestion/ingest_raw_olist.py

echo "Local ingestion from Kaggle CSVs completed."

