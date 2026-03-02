#!/usr/bin/env bash
# Download Olist dataset from Kaggle and ingest via GCS -> BigQuery.
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

if [ -z "${GCS_BUCKET:-}" ]; then
  echo "GCS_BUCKET is not set. Set it in .env before running this script."
  exit 1
fi

echo "Downloading Olist dataset from Kaggle into ${DATA_DIR} ..."
mkdir -p "${DATA_DIR}"
kaggle datasets download -d olistbr/brazilian-ecommerce -p "${DATA_DIR}" --unzip --force

echo "Uploading CSVs to GCS and ingesting into BigQuery (raw_olist) ..."
python gcs_pipeline/upload_and_ingest_raw_olist.py

echo "GCS-based ingestion from Kaggle CSVs completed."

