"""
Supabase Client Wrapper

Provides a clean interface for Supabase database operations,
handling connection management and error handling.
"""

from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from utils.config import get_settings
from utils.logger import get_logger
from datetime import datetime


class SupabaseClient:
    """Wrapper for Supabase client with error handling and connection management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Supabase client"""
        try:
            if not self.settings.supabase_url or not self.settings.supabase_key:
                self.logger.warning("Supabase credentials not configured")
                return
            
            self.client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_key
            )
            self.logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if Supabase client is connected"""
        return self.client is not None
    
    # ============ Jobs ============

    async def insert_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a job into the jobs table"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            result = self.client.table('jobs').insert(job_data).execute()
            if result.data:
                self.logger.info(f"Job inserted: {result.data[0].get('id')}")
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to insert job: {e}")
            raise
    
    async def update_job(self, job_id: str, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a job in the jobs table"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            result = self.client.table('jobs').update(job_data).eq('id', job_id).execute()
            if result.data:
                self.logger.info(f"Job updated: {job_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to update job {job_id}: {e}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            result = self.client.table('jobs').select('*').eq('id', job_id).execute()
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get job {job_id}: {e}")
            raise
    
    async def get_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs with optional status filter"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            query = self.client.table('jobs').select('*')
            if status:
                query = query.eq('status', status)
            
            result = query.limit(limit).execute()
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"Failed to get jobs: {e}")
            raise
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            result = self.client.table('jobs').delete().eq('id', job_id).execute()
            success = len(result.data) > 0
            if success:
                self.logger.info(f"Job deleted: {job_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete job {job_id}: {e}")
            raise
    
    # ============ Tasks ============

    async def insert_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a task into the tasks table"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            result = self.client.table('tasks').insert(task_data).execute()
            if result.data:
                self.logger.info(f"Task inserted: {result.data[0].get('id')}")
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to insert task: {e}")
            raise
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task in the tasks table"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            result = self.client.table('tasks').update(task_data).eq('id', task_id).execute()
            if result.data:
                self.logger.info(f"Task updated: {task_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to update task {task_id}: {e}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            result = self.client.table('tasks').select('*').eq('id', task_id).execute()
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get task {task_id}: {e}")
            raise
    
    async def get_tasks(self, is_active: Optional[bool] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tasks with optional active filter"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            query = self.client.table('tasks').select('*')
            if is_active is not None:
                query = query.eq('is_active', is_active)
            
            result = query.limit(limit).execute()
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"Failed to get tasks: {e}")
            raise
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            result = self.client.table('tasks').delete().eq('id', task_id).execute()
            success = len(result.data) > 0
            if success:
                self.logger.info(f"Task deleted: {task_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete task {task_id}: {e}")
            raise
    
    async def backup_all_data(self) -> Dict[str, Any]:
        """Backup all jobs and tasks data"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            jobs = await self.get_jobs(limit=1000)
            tasks = await self.get_tasks(limit=1000)
            
            backup_data = {
                "jobs": jobs,
                "tasks": tasks,
                "timestamp": str(datetime.now()),
                "total_jobs": len(jobs),
                "total_tasks": len(tasks)
            }
            
            self.logger.info(f"Backup completed: {len(jobs)} jobs, {len(tasks)} tasks")
            return backup_data
            
        except Exception as e:
            self.logger.error(f"Failed to backup data: {e}")
            raise
    
    async def restore_jobs(self, jobs_data: List[Dict[str, Any]]) -> int:
        """Restore jobs from backup data"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            # Clear existing jobs
            self.client.table('jobs').delete().neq('id', '').execute()
            
            # Insert backup jobs
            if jobs_data:
                result = self.client.table('jobs').insert(jobs_data).execute()
                restored_count = len(result.data) if result.data else 0
                self.logger.info(f"Restored {restored_count} jobs")
                return restored_count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to restore jobs: {e}")
            raise
    
    async def restore_tasks(self, tasks_data: List[Dict[str, Any]]) -> int:
        """Restore tasks from backup data"""
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            
            # Clear existing tasks
            self.client.table('tasks').delete().neq('id', '').execute()
            
            # Insert backup tasks
            if tasks_data:
                result = self.client.table('tasks').insert(tasks_data).execute()
                restored_count = len(result.data) if result.data else 0
                self.logger.info(f"Restored {restored_count} tasks")
                return restored_count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to restore tasks: {e}")
            raise


# Global instance
_supabase_client: Optional[SupabaseClient] = None

def get_supabase_client() -> SupabaseClient:
    """Get the global Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
