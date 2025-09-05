"""
Storage Interface

Provides a unified interface for storing and retrieving data,
supporting both file-based and Supabase backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from utils.config import get_settings
from utils.logger import get_logger
from db.supabase_client import get_supabase_client
from datetime import datetime


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Store a job"""
        pass
    
    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID"""
        pass
    
    @abstractmethod
    async def get_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get jobs with optional status filter"""
        pass
    
    @abstractmethod
    async def update_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """Update a job"""
        pass
    
    @abstractmethod
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        pass
    
    @abstractmethod
    async def store_task(self, task_data: Dict[str, Any]) -> bool:
        """Store a task"""
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        pass
    
    @abstractmethod
    async def get_tasks(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get tasks with optional active filter"""
        pass
    
    @abstractmethod
    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Update a task"""
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        pass
    
    @abstractmethod
    async def backup_data(self) -> Dict[str, Any]:
        """Backup all data"""
        pass
    
    @abstractmethod
    async def restore_data(self, backup_data: Dict[str, Any]) -> bool:
        """Restore data from backup"""
        pass


class FileStorageBackend(StorageBackend):
    """File-based storage backend using JSON files"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.jobs_file = self.settings.messaging_backup_file
        self.tasks_file = self.settings.scheduler_backup_file
        self._jobs_cache: Dict[str, Dict[str, Any]] = {}
        self._tasks_cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load data from files into cache"""
        import json
        import aiofiles
        import asyncio
        
        async def load_file(filename: str) -> Dict[str, Any]:
            try:
                async with aiofiles.open(filename, 'r') as f:
                    content = await f.read()
                    return json.loads(content) if content else {}
            except FileNotFoundError:
                return {}
            except Exception as e:
                self.logger.error(f"Failed to load {filename}: {e}")
                return {}
        
        # Load jobs
        try:
            jobs_data = asyncio.run(load_file(self.jobs_file))
            self._jobs_cache = jobs_data.get('jobs', {})
        except Exception as e:
            self.logger.error(f"Failed to load jobs cache: {e}")
            self._jobs_cache = {}
        
        # Load tasks
        try:
            tasks_data = asyncio.run(load_file(self.tasks_file))
            self._tasks_cache = {task['id']: task for task in tasks_data.get('tasks', {}).values()}
        except Exception as e:
            self.logger.error(f"Failed to load tasks cache: {e}")
            self._tasks_cache = {}
    
    async def _save_jobs(self):
        """Save jobs to file"""
        import json
        import aiofiles
        
        try:
            backup_data = {
                "jobs": self._jobs_cache,
                "timestamp": str(datetime.now())
            }
            async with aiofiles.open(self.jobs_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save jobs: {e}")
    
    async def _save_tasks(self):
        """Save tasks to file"""
        import json
        import aiofiles
        
        try:
            backup_data = {
                "tasks": self._tasks_cache,
                "timestamp": str(datetime.now())
            }
            async with aiofiles.open(self.tasks_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
    
    async def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Store a job"""
        try:
            job_id = job_data.get('id')
            if job_id:
                self._jobs_cache[job_id] = job_data
                await self._save_jobs()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to store job: {e}")
            return False
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID"""
        return self._jobs_cache.get(job_id)
    
    async def get_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get jobs with optional status filter"""
        jobs = list(self._jobs_cache.values())
        if status:
            jobs = [job for job in jobs if job.get('status') == status]
        return jobs
    
    async def update_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """Update a job"""
        try:
            if job_id in self._jobs_cache:
                self._jobs_cache[job_id].update(job_data)
                await self._save_jobs()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update job: {e}")
            return False
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        try:
            if job_id in self._jobs_cache:
                del self._jobs_cache[job_id]
                await self._save_jobs()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete job: {e}")
            return False
    
    async def store_task(self, task_data: Dict[str, Any]) -> bool:
        """Store a task"""
        try:
            task_id = task_data.get('id')
            if task_id:
                self._tasks_cache[task_id] = task_data
                await self._save_tasks()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to store task: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        return self._tasks_cache.get(task_id)
    
    async def get_tasks(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get tasks with optional active filter"""
        tasks = list(self._tasks_cache.values())
        if is_active is not None:
            tasks = [task for task in tasks if task.get('is_active') == is_active]
        return tasks
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Update a task"""
        try:
            if task_id in self._tasks_cache:
                self._tasks_cache[task_id].update(task_data)
                await self._save_tasks()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update task: {e}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            if task_id in self._tasks_cache:
                del self._tasks_cache[task_id]
                await self._save_tasks()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete task: {e}")
            return False
    
    async def backup_data(self) -> Dict[str, Any]:
        """Backup all data"""
        return {
            "jobs": self._jobs_cache,
            "tasks": self._tasks_cache,
            "timestamp": str(datetime.now()),
            "total_jobs": len(self._jobs_cache),
            "total_tasks": len(self._tasks_cache)
        }
    
    async def restore_data(self, backup_data: Dict[str, Any]) -> bool:
        """Restore data from backup"""
        try:
            self._jobs_cache = backup_data.get('jobs', {})
            self._tasks_cache = {task['id']: task for task in backup_data.get('tasks', {}).values()}
            
            await self._save_jobs()
            await self._save_tasks()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore data: {e}")
            return False


class SupabaseStorageBackend(StorageBackend):
    """Supabase-based storage backend"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.client = get_supabase_client()
    
    async def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Store a job"""
        try:
            result = await self.client.insert_job(job_data)
            return result is not None
        except Exception as e:
            self.logger.error(f"Failed to store job: {e}")
            return False
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID"""
        try:
            return await self.client.get_job(job_id)
        except Exception as e:
            self.logger.error(f"Failed to get job: {e}")
            return None
    
    async def get_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get jobs with optional status filter"""
        try:
            return await self.client.get_jobs(status=status)
        except Exception as e:
            self.logger.error(f"Failed to get jobs: {e}")
            return []
    
    async def update_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """Update a job"""
        try:
            result = await self.client.update_job(job_id, job_data)
            return result is not None
        except Exception as e:
            self.logger.error(f"Failed to update job: {e}")
            return False
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        try:
            return await self.client.delete_job(job_id)
        except Exception as e:
            self.logger.error(f"Failed to delete job: {e}")
            return False
    
    async def store_task(self, task_data: Dict[str, Any]) -> bool:
        """Store a task"""
        try:
            result = await self.client.insert_task(task_data)
            return result is not None
        except Exception as e:
            self.logger.error(f"Failed to store task: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        try:
            return await self.client.get_task(task_id)
        except Exception as e:
            self.logger.error(f"Failed to get task: {e}")
            return None
    
    async def get_tasks(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get tasks with optional active filter"""
        try:
            return await self.client.get_tasks(is_active=is_active)
        except Exception as e:
            self.logger.error(f"Failed to get tasks: {e}")
            return []
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Update a task"""
        try:
            result = await self.client.update_task(task_id, task_data)
            return result is not None
        except Exception as e:
            self.logger.error(f"Failed to update task: {e}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            return await self.client.delete_task(task_id)
        except Exception as e:
            self.logger.error(f"Failed to delete task: {e}")
            return False
    
    async def backup_data(self) -> Dict[str, Any]:
        """Backup all data"""
        try:
            return await self.client.backup_all_data()
        except Exception as e:
            self.logger.error(f"Failed to backup data: {e}")
            return {}
    
    async def restore_data(self, backup_data: Dict[str, Any]) -> bool:
        """Restore data from backup"""
        try:
            jobs_data = backup_data.get('jobs', [])
            tasks_data = backup_data.get('tasks', [])
            
            await self.client.restore_jobs(jobs_data)
            await self.client.restore_tasks(tasks_data)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore data: {e}")
            return False


def get_storage_backend() -> StorageBackend:
    """Get the appropriate storage backend based on configuration"""
    settings = get_settings()
    
    if settings.storage_backend.lower() == "supabase":
        return SupabaseStorageBackend()
    else:
        return FileStorageBackend()
