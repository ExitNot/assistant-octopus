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

# Check for poetry
if ! command -v poetry &> /dev/null; then
  echo "Poetry is not installed. Please install poetry first."
  exit 1
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

# Run CLI
echo "Starting Assistant Octopus CLI..."
poetry run python cli_server.py
