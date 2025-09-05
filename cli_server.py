#!/usr/bin/env python3
"""
CLI Server Interface for Assistant Octopus

Provides an interactive CLI interface for managing the server with:
- Project building
- Server startup
- Backup loading
- Command management (restart, shutdown)
"""

import asyncio
import subprocess
import sys
import signal
import os
from typing import Optional, Dict, Any
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings

from services.messaging.factory import MessagingServiceFactory
from services.scheduler import SchedulerService, TaskService
from utils.config import get_settings
from utils.logger import get_logger
from db.storage import get_storage_backend
from utils.logging_config import system_logging


class ServerManager:
    """Manages the server lifecycle and CLI interface"""
    
    def __init__(self):
        self.settings = get_settings()
        system_logging("INFO")
        self.logger = get_logger(__name__)
        self.server_process: Optional[subprocess.Popen] = None
        self.messaging_service = None
        self.scheduler_service = None
        self.task_service = None
        self.storage_backend = get_storage_backend()
        self.is_running = False
        
        # Setup key bindings
        self.kb = KeyBindings()
        
        # Setup command completer
        self.commands = [
            'help', 'status', 'build', 'start', 'restart', 'shutdown', 
            'backup', 'load', 'logs', 'clear', 'exit', 'quit'
        ]
        self.completer = WordCompleter(self.commands, ignore_case=True)
        
        # Setup styles
        self.style = Style.from_dict({
            'prompt': 'ansicyan bold',
            'error': 'ansired bold',
            'success': 'ansigreen bold',
            'warning': 'ansiyellow bold',
            'info': 'ansiblue',
        })
        
        # Setup prompt session
        self.session = PromptSession(
            completer=self.completer,
            style=self.style,
            key_bindings=self.kb
        )

    async def initialize_services(self):
        """Initialize messaging and scheduler services"""
        try:
            # Initialize messaging service
            self.messaging_service = await MessagingServiceFactory.initialize_service()
            self.logger.info("Messaging service initialized")
            
            # Initialize scheduler service
            self.scheduler_service = SchedulerService(self.messaging_service)
            await self.scheduler_service.start()
            self.logger.info("Scheduler service initialized")
            
            # Initialize task service
            self.task_service = TaskService(self.scheduler_service)
            self.logger.info("Task service initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise

    async def load_backups(self):
        """Load messages and schedules from storage"""
        try:
            # Load jobs from storage
            jobs = await self.storage_backend.get_jobs()
            if jobs:
                # Restore jobs to messaging service
                for job_data in jobs:
                    if job_data.get('status') == 'pending':
                        # Re-queue pending jobs
                        from models.messaging_models import Job
                        job = Job.from_dict(job_data)
                        await self.messaging_service.job_queue.enqueue(job)
                self.logger.info(f"Loaded {len(jobs)} jobs from storage")
            
            # Load tasks from storage
            tasks = await self.storage_backend.get_tasks()
            if tasks:
                # Restore tasks to task service
                for task_data in tasks:
                    from models.task_models import Task
                    task = Task.from_dict(task_data)
                    self.task_service._tasks[task.id] = task
                    
                    # Re-schedule active tasks
                    if task.is_active:
                        await self.scheduler_service.schedule_task(task)
                self.logger.info(f"Loaded {len(tasks)} tasks from storage")
                
        except Exception as e:
            self.logger.error(f"Failed to load backups: {e}")

    async def backup_data(self):
        """Backup messages and schedules to storage"""
        try:
            # Get current jobs from messaging service
            jobs_data = []
            if hasattr(self.messaging_service.job_queue, '_jobs'):
                for job in self.messaging_service.job_queue._jobs.values():
                    jobs_data.append(job.to_dict())
            
            # Store jobs
            for job_data in jobs_data:
                await self.storage_backend.store_job(job_data)
            
            # Get current tasks from task service
            tasks_data = []
            for task in self.task_service._tasks.values():
                tasks_data.append(task.to_dict())
            
            # Store tasks
            for task_data in tasks_data:
                await self.storage_backend.store_task(task_data)
            
            self.logger.info(f"Backed up {len(jobs_data)} jobs and {len(tasks_data)} tasks")
                
        except Exception as e:
            self.logger.error(f"Failed to backup data: {e}")

    def build_project(self) -> bool:
        """Build the project using poetry"""
        try:
            self.logger.info("Building project with poetry...")
            result = subprocess.run(
                ['poetry', 'install'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.logger.info("Project built successfully")
                return True
            else:
                self.logger.error(f"Build failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Build error: {e}")
            return False

    def start_server(self) -> bool:
        """Start the FastAPI server"""
        try:
            if self.server_process and self.server_process.poll() is None:
                self.logger.warning("Server is already running")
                return True
            
            self.logger.info("Starting FastAPI server...")
            self.server_process = subprocess.Popen(
                ['poetry', 'run', 'uvicorn', 'services.api:app', '--reload'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.is_running = True
            self.logger.info("Server started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop the FastAPI server"""
        try:
            if self.server_process and self.server_process.poll() is None:
                self.logger.info("Stopping server...")
                self.server_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Server didn't stop gracefully, forcing...")
                    self.server_process.kill()
                
                self.is_running = False
                self.logger.info("Server stopped")
                return True
            else:
                self.logger.info("Server is not running")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop server: {e}")
            return False

    async def restart_server(self) -> bool:
        """Restart the server with backup"""
        try:
            self.logger.info("Restarting server...")
            
            # Backup current data
            await self.backup_data()
            
            # Stop server
            if not self.stop_server():
                return False
            
            # Start server
            if not self.start_server():
                return False
            
            # Load backups
            await self.load_backups()
            
            self.logger.info("Server restarted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restart server: {e}")
            return False

    async def shutdown_server(self) -> bool:
        """Shutdown server with backup"""
        try:
            self.logger.info("Shutting down server...")
            
            # Backup current data
            await self.backup_data()
            
            # Stop server
            if not self.stop_server():
                return False
            
            # Shutdown services
            if self.scheduler_service:
                await self.scheduler_service.stop()
            
            if self.messaging_service:
                await MessagingServiceFactory.shutdown_service()
            
            self.logger.info("Server shutdown complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown server: {e}")
            return False

    def get_server_logs(self, lines: int = 50) -> str:
        """Get recent server logs"""
        try:
            if not self.server_process or self.server_process.poll() is not None:
                return "Server is not running"
            
            # For now, return a simple status
            return f"Server PID: {self.server_process.pid}, Status: {'Running' if self.is_running else 'Stopped'}"
            
        except Exception as e:
            return f"Error getting logs: {e}"

    def get_status(self) -> Dict[str, Any]:
        """Get current server status"""
        return {
            'server_running': self.is_running,
            'server_pid': self.server_process.pid if self.server_process else None,
            'messaging_service': self.messaging_service is not None,
            'scheduler_service': self.scheduler_service is not None,
            'task_service': self.task_service is not None,
            'storage_backend': self.settings.storage_backend,
            'timestamp': datetime.now().isoformat()
        }

    def show_help(self):
        """Show help information"""
        help_text = """
Available Commands:
  help      - Show this help message
  status    - Show server status
  build     - Build project with poetry
  start     - Start the server
  restart   - Restart server with backup
  shutdown  - Shutdown server with backup
  backup    - Backup current data
  load      - Load data from storage
  logs      - Show server logs
  clear     - Clear screen
  exit/quit - Exit the CLI

Examples:
  build     - Build the project
  start     - Start the server
  restart   - Restart with data backup
  shutdown  - Shutdown with data backup

Storage Backend: {storage_backend}
""".format(storage_backend=self.settings.storage_backend.upper())
        print(help_text)

    def show_status(self):
        """Show current status"""
        status = self.get_status()
        print(f"\nServer Status:")
        print(f"  Running: {status['server_running']}")
        print(f"  PID: {status['server_pid']}")
        print(f"  Messaging Service: {status['messaging_service']}")
        print(f"  Scheduler Service: {status['scheduler_service']}")
        print(f"  Task Service: {status['task_service']}")
        print(f"  Storage Backend: {status['storage_backend']}")
        print(f"  Timestamp: {status['timestamp']}")

    async def run(self):
        """Main CLI loop"""
        print("🤖 Assistant Octopus Server Manager")
        print(f"Storage Backend: {self.settings.storage_backend.upper()}")
        print("Type 'help' for available commands")
        print("-" * 50)
        
        # Initialize services
        try:
            await self.initialize_services()
            await self.load_backups()
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            print(f"❌ Initialization failed: {e}")
            return
        
        # Main command loop
        while True:
            try:
                # Create prompt with status indicator
                status_indicator = "🟢" if self.is_running else "🔴"
                prompt_text = FormattedText([
                    ('class:prompt', f'{status_indicator} octopus> ')
                ])
                
                command = await self.session.prompt_async(prompt_text)
                command = command.strip().lower()
                
                if not command:
                    continue
                
                # Process commands
                if command in ['exit', 'quit']:
                    await self.shutdown_server()
                    print("👋 Goodbye!")
                    break
                    
                elif command == 'help':
                    self.show_help()
                    
                elif command == 'status':
                    self.show_status()
                    
                elif command == 'build':
                    if self.build_project():
                        print("✅ Build completed successfully")
                    else:
                        print("❌ Build failed")
                        
                elif command == 'start':
                    if self.start_server():
                        print("✅ Server started successfully")
                    else:
                        print("❌ Failed to start server")
                        
                elif command == 'restart':
                    if await self.restart_server():
                        print("✅ Server restarted successfully")
                    else:
                        print("❌ Failed to restart server")
                        
                elif command == 'shutdown':
                    if await self.shutdown_server():
                        print("✅ Server shutdown successfully")
                    else:
                        print("❌ Failed to shutdown server")
                        
                elif command == 'backup':
                    await self.backup_data()
                    print("✅ Data backed up successfully")
                    
                elif command == 'load':
                    await self.load_backups()
                    print("✅ Data loaded from storage")
                    
                elif command == 'logs':
                    logs = self.get_server_logs()
                    print(f"📋 Server Logs:\n{logs}")
                    
                elif command == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    
                else:
                    print(f"❓ Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted by user")
                continue
            except Exception as e:
                self.logger.error(f"Command error: {e}")
                print(f"❌ Error: {e}")


async def main():
    """Main entry point"""
    manager = ServerManager()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"\n⚠️  Received signal {signum}, shutting down...")
        asyncio.create_task(manager.shutdown_server())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await manager.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
