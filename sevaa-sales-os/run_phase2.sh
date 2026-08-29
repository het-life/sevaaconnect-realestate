#!/usr/bin/env bash
set -euo pipefail
uvicorn backend.phase2:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
