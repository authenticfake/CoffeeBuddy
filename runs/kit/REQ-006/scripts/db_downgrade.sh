#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL env var is required" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_DIR="${ROOT_DIR}/src/storage/sql"

for script in $(ls "${SQL_DIR}"/*.down.sql | sort -r); do
  echo "Reverting ${script}"
  psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "${script}"
done