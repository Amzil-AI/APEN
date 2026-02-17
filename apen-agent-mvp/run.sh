#!/usr/bin/env bash
# Run APEN Agent MVP API (development)
set -e
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
. .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port "${PORT:-8000}"
