#!/bin/bash

# Assistant Octopus CLI Launcher

# Check for .env file
if [ ! -f .env ]; then
  echo ".env file not found! Please create it with required environment variables."
  echo "Required variables:"
  echo "  - OLLAMA_API_URL"
  echo "  - TELERGRAM_BOT_TOKEN"
  echo "  - SUPERVISOR_API_URL"
  echo "  - IMAGE_ROUTER_API_KEY"
  echo "  - TOGETHER_AI_API_KEY"
  echo ""
  echo "Optional variables:"
  echo "  - STORAGE_BACKEND (file or supabase)"
  echo "  - SUPABASE_URL (if using supabase backend)"
  echo "  - SUPABASE_KEY (if using supabase backend)"
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

echo "Starting Assistant Octopus CLI..."
python cli_server.py
