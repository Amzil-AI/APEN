#!/bin/bash
# Railway start script - runs from root directory

# Activate the virtual environment that Railway created
source /opt/venv/bin/activate

# Navigate to app directory
cd apen-agent-mvp

# Start the FastAPI app
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
