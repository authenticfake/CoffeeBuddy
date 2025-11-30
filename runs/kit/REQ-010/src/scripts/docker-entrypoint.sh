#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=${PYTHONPATH:-/app/src}

uvicorn coffeebuddy.infrastructure.runtime.container:app \
  --host "${SERVICE_HOST:-0.0.0.0}" \
  --port "${SERVICE_PORT:-8080}"