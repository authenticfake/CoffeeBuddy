#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_DIR="${ROOT_DIR}/src/storage/sql"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL must be set to run migrations" >&2
  exit 1
fi

for migration in $(ls "${SQL_DIR}"/V*.up.sql | sort); do
  echo "Applying ${migration}"
  psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "${migration}"
done

echo "Migrations applied successfully."