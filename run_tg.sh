#!/bin/bash

# Run Telegram bot
export PYTHONPATH=$(pwd)

echo "Activating virtual environment..."
. .venv/bin/activate

# Sync dependencies using uv
echo "Syncing dependencies with uv..."
python -m uv sync || true

echo "Starting Telegram bot..."
python clients/tg_client.py