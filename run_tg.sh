#!/bin/bash

# Run Telegram bot
export PYTHONPATH=$(pwd)
echo "Starting Telegram bot..."
poetry run python clients/tg_client.py