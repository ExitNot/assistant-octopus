# Assistant Octopus CLI Interface

This CLI interface provides an enhanced experience for running and managing the Assistant Octopus server with support for both file-based and Supabase storage backends.

## Features

- **Interactive CLI**: Beautiful command-line interface with command completion
- **Project Building**: Automatic dependency installation with Poetry
- **Server Management**: Start, stop, restart, and shutdown server
- **Data Persistence**: Support for both file-based and Supabase storage
- **Backup Management**: Automatic backup and restore of messages and schedules
- **Real-time Status**: Live server status indicators

## Installation

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Configure Environment**:
   Create a `.env` file with the required variables:
   ```env
   # Required variables
   OLLAMA_API_URL=your_ollama_url
   TELERGRAM_BOT_TOKEN=your_telegram_token
   SUPERVISOR_API_URL=your_supervisor_url
   IMAGE_ROUTER_API_KEY=your_image_router_key
   TOGETHER_AI_API_KEY=your_together_ai_key
   
   # Storage configuration
   STORAGE_BACKEND=file  # or "supabase"
   
   # Supabase configuration (if using supabase backend)
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_service_key
   ```

## Usage

### Quick Start

Run the CLI launcher:
```bash
chmod +x run_cli.sh
./run_cli.sh
```

Or run directly with Poetry:
```bash
poetry run python cli_server.py
```

### Available Commands

| Command | Description |
|---------|-------------|
| `help` | Show help information |
| `status` | Show server status |
| `build` | Build project with Poetry |
| `start` | Start the server |
| `restart` | Restart server with backup |
| `shutdown` | Shutdown server with backup |
| `backup` | Backup current data |
| `load` | Load data from storage |
| `logs` | Show server logs |
| `clear` | Clear screen |
| `exit` / `quit` | Exit the CLI |

### Storage Backends

#### File Storage (Default)
- Uses JSON files for data persistence
- Files: `jobs_backup.json`, `tasks_backup.json`
- Good for development and simple deployments

#### Supabase Storage
- Uses Supabase PostgreSQL database
- Better for production and multi-instance deployments
- Requires Supabase setup

## Supabase Setup

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and service key

### 2. Set Up Database Schema
1. Go to your Supabase project SQL editor
2. Run the SQL from `supabase_schema.sql`
3. This creates the required tables and indexes

### 3. Configure Environment
Update your `.env` file:
```env
STORAGE_BACKEND=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_key_here
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_BACKEND` | `file` | Storage backend: `file` or `supabase` |
| `SUPABASE_URL` | - | Supabase project URL |
| `SUPABASE_KEY` | - | Supabase service key |
| `MESSAGING_BACKUP_FILE` | `jobs_backup.json` | File for job backups |
| `SCHEDULER_BACKUP_FILE` | `tasks_backup.json` | File for task backups |

## Workflow Examples

### Development Workflow
```bash
# Start CLI
./run_cli.sh

# Build and start
octopus> build
octopus> start

# Check status
octopus> status

# Restart with backup
octopus> restart

# Shutdown
octopus> shutdown
```

### Production Workflow
```bash
# Set up Supabase backend
# Update .env with STORAGE_BACKEND=supabase

# Start CLI
./run_cli.sh

# Build and start
octopus> build
octopus> start

# Monitor and manage
octopus> status
octopus> logs
```

## Data Migration

### From File to Supabase
1. Set `STORAGE_BACKEND=file` and start CLI
2. Run `load` to load existing file data
3. Change `STORAGE_BACKEND=supabase` in `.env`
4. Restart CLI and run `backup` to migrate to Supabase

### From Supabase to File
1. Set `STORAGE_BACKEND=supabase` and start CLI
2. Run `backup` to get current data
3. Change `STORAGE_BACKEND=file` in `.env`
4. Restart CLI and run `load` to restore to files

## Troubleshooting

### Common Issues

1. **Poetry not found**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Supabase connection failed**:
   - Check your Supabase URL and key
   - Ensure RLS policies are configured
   - Verify database schema is set up

3. **Permission denied on run_cli.sh**:
   ```bash
   chmod +x run_cli.sh
   ```

4. **Missing .env file**:
   - Copy from `.env.example` if available
   - Create with required variables

### Logs and Debugging

- Check CLI output for error messages
- Use `logs` command to see server status
- Check `logs/` directory for detailed logs
- Enable debug logging with `LOG_LEVEL=DEBUG`

## Architecture

The CLI uses a modular architecture:

```
CLI Server Manager
├── Storage Backend (File/Supabase)
├── Messaging Service
├── Scheduler Service
└── Task Service
```

### Storage Interface
- Abstract `StorageBackend` interface
- `FileStorageBackend` for JSON file storage
- `SupabaseStorageBackend` for database storage
- Automatic backend selection based on configuration

### Service Integration
- Integrates with existing messaging and scheduler services
- Maintains compatibility with current API endpoints
- Provides unified backup/restore functionality

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Test with both storage backends

## License

MIT License - see LICENSE file for details
