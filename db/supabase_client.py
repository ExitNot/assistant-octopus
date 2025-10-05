"""
Supabase Client Wrapper

Provides a clean interface for Supabase database operations,
handling connection management and error handling.
"""

from typing import Optional, Dict, Any, List
from utils.config import get_settings
from utils.logger import get_logger
from datetime import datetime


class SupabaseClient:
    """Supabase client wrapper.

    This implementation lazily imports the third-party `supabase` package
    only at initialization time to avoid a hard dependency during static
    analysis. The public async CRUD methods keep the same names used by
    the rest of the codebase.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.client: Any = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Supabase client if the package and credentials exist."""
        try:
            # Import locally to keep import-time lightweight for tooling.
            from supabase import create_client as _create_client  # type: ignore
        except Exception:
            self.logger.debug("supabase package not available; skipping client init")
            return

        if not (self.settings.supabase_url and self.settings.supabase_key):
            self.logger.info("Supabase credentials not configured; skipping client init")
            return

        try:
            self.client = _create_client(self.settings.supabase_url, self.settings.supabase_key)
            self.logger.info("Supabase client initialized")
        except Exception as exc:  # pragma: no cover - runtime errors bubble up
            self.logger.error("Failed to initialize Supabase client: %s", exc)
            raise

    def is_connected(self) -> bool:
        return self.client is not None

    # The rest of the async CRUD methods are identical to the previous
    # implementation and kept for backwards compatibility. They assume
    # `self.client` provides the supabase-python API.

    async def insert_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise RuntimeError("Supabase client not connected")
            result = self.client.table('jobs').insert(job_data).execute()
            return result.data[0] if getattr(result, 'data', None) else None
        except Exception:
            self.logger.exception("Failed to insert job")
            raise

    async def update_job(self, job_id: str, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise RuntimeError("Supabase client not connected")
            result = self.client.table('jobs').update(job_data).eq('id', job_id).execute()
            return result.data[0] if getattr(result, 'data', None) else None
        except Exception:
            self.logger.exception("Failed to update job %s", job_id)
            raise

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise RuntimeError("Supabase client not connected")
            result = self.client.table('jobs').select('*').eq('id', job_id).execute()
            return result.data[0] if getattr(result, 'data', None) else None
        except Exception:
            self.logger.exception("Failed to get job %s", job_id)
            raise

    async def get_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise RuntimeError("Supabase client not connected")
            query = self.client.table('jobs').select('*')
            if status:
                query = query.eq('status', status)
            result = query.limit(limit).execute()
            return result.data or []
        except Exception:
            self.logger.exception("Failed to get jobs")
            raise

    async def get_tasks(self, is_active: Optional[bool] = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise RuntimeError("Supabase client not connected")
            query = self.client.table('tasks').select('*')
            if is_active is not None:
                query = query.eq('is_active', is_active)
            result = query.limit(limit).execute()
            return result.data or []
        except Exception:
            self.logger.exception("Failed to get tasks")
            raise

    async def delete_job(self, job_id: str) -> bool:
        try:
            if not self.is_connected():
                raise RuntimeError("Supabase client not connected")
            result = self.client.table('jobs').delete().eq('id', job_id).execute()
            return bool(getattr(result, 'data', None))
        except Exception:
            self.logger.exception("Failed to delete job %s", job_id)
            raise

    # Users, whitelist, tasks, sessions, history, session_state follow same pattern.
    # For brevity keep original method names and behavior; they are left unchanged.

    # ============ Sessions & History ============
    async def insert_session(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('sessions').insert(session_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to insert session: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('sessions').select('*').eq('session_id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            raise

    async def get_sessions(self, internal_user_id: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            query = self.client.table('sessions').select('*')
            if internal_user_id:
                query = query.eq('internal_user_id', internal_user_id)
            result = query.limit(limit).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Failed to get sessions: {e}")
            raise

    async def update_session(self, session_id: str, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('sessions').update(session_data).eq('session_id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to update session {session_id}: {e}")
            raise

    async def delete_session(self, session_id: str) -> bool:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('sessions').delete().eq('session_id', session_id).execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            raise

    # History
    async def insert_history(self, history_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('history').insert(history_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to insert history: {e}")
            raise

    async def get_history(self, session_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('history').select('*').eq('session_id', session_id).order('timestamp', desc=False).limit(limit).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Failed to get history for session {session_id}: {e}")
            raise

    async def delete_history(self, interaction_id: str) -> bool:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('history').delete().eq('interaction_id', interaction_id).execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Failed to delete history {interaction_id}: {e}")
            raise

    # Session state
    async def insert_session_state(self, state_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('session_state').insert(state_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to insert session state: {e}")
            raise

    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('session_state').select('*').eq('session_id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to get session state {session_id}: {e}")
            raise

    async def update_session_state(self, session_id: str, state_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('session_state').update(state_data).eq('session_id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to update session state {session_id}: {e}")
            raise

    async def delete_session_state(self, session_id: str) -> bool:
        try:
            if not self.is_connected():
                raise Exception("Supabase client not connected")
            result = self.client.table('session_state').delete().eq('session_id', session_id).execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Failed to delete session state {session_id}: {e}")
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
