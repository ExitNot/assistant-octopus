#!/bin/bash

# Check for .env file
if [ ! -f .env ]; then
  echo ".env file not found! Please create it with OLLAMA_API_URL set."
  exit 1
fi

# Check for poetry
if ! command -v poetry &> /dev/null; then
  echo "Poetry is not installed. Please install poetry first."
  exit 1
fi

poetry install

# Run API
echo "Starting FastAPI app..."
poetry run uvicorn api.api:app --reload 