#!/bin/bash

# Check for .env file
if [ ! -f .env ]; then
  echo ".env file not found! Please create it with OLLAMA_API_URL set."
  exit 1
fi

# Create and activate virtualenv using uv (if missing)
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment with uv..."
  uv venv .venv
fi

echo "Activating virtual environment..."
. .venv/bin/activate

# Sync dependencies using uv
echo "Syncing dependencies with uv..."
uv sync || true

# Run API
echo "Starting FastAPI app..."
python -m uvicorn api.api:app --reload