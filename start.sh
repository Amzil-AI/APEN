#!/bin/bash
# Railway start script - runs from root directory

cd apen-agent-mvp
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
