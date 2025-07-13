# Assistant Octopus

Assistant Octopus is a personal assistant built with a supervisor agent architecture. Its goal is to help manage daily planning, tasks, notes, and habits, integrating with multiple data sources (Obsidian, calendar, etc.) and interfaces (Telegram, CLI, voice).

## Key Features

- Supervisor agent orchestrates specialized sub-agents (planning, knowledge, habits, notifications).
- Integrates with Telegram (first), CLI, and voice (Kyutai STT planned).
- Persistent memory using Redis and Supabase.
- Knowledge management via Obsidian vault and vector DB (Pinecone).
- Modular, extensible architecture with FastAPI backend.

## Project Structure

- `agents/`   — Contains agent logic and orchestration modules
- `models/`   — Contains Pydantic models and data schemas
- `services/` — Contains business logic and service layer code
- `clients/`  — Contains clients logic (Cli, Telegram)
- `utils/`    — Contains utility functions and helpers
- `tests/`    — Contains tests

## Requirements
Python 3.11+
Poetry for dependency management
Redis 6+ (for session/caching)
Supabase (PostgreSQL 14+) for persistent storage
Ollama (local LLM backend)
python-telegram-bot (for Telegram integration)

## How to Run
1. Clone the repository
```
git clone <repo-url>
cd assistant-octopus
```
2. Install dependencies
```
poetry install
```
3. Set up enviroment variables
Create a `.env` file with your configuration. Example of `.env` file can be found under `.env.example`
4. Ensure that Ollama, ~~Redis~~ and ~~Supabase~~ are running
5. Start the FastAPI server
```
./run.sh
```
6. Start telegram client
```
./run_tg.sh
```

## Current status
See `docs/mvp-generated-tasks.md` for detailed roadmap and progress.