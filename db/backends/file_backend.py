"""File-based storage backend implementation."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from db.backends.base import StorageBackend
from utils.config import get_settings
from utils.logger import get_logger


class FileStorageBackend(StorageBackend):
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.jobs_file = self.settings.messaging_backup_file
        self.tasks_file = self.settings.scheduler_backup_file
        self.users_file = self.settings.user_backup_file
        self.whitelist_file = self.settings.whitelist_backup_file
        self.sessions_file = self.settings.session_backup_file
        self.history_file = self.settings.history_backup_file
        self.session_state_file = self.settings.session_state_backup_file

        self._jobs_cache: Dict[str, Dict[str, Any]] = {}
        self._tasks_cache: Dict[str, Dict[str, Any]] = {}
        self._users_cache: Dict[str, Dict[str, Any]] = {}
        self._whitelist_cache: Dict[str, Dict[str, Any]] = {}
        self._sessions_cache: Dict[str, Dict[str, Any]] = {}
        self._history_cache: Dict[str, Dict[str, Any]] = {}
        self._session_state_cache: Dict[str, Dict[str, Any]] = {}

        self._load_cache()

    def _load_cache(self):
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

        try:
            jobs_data = asyncio.run(load_file(self.jobs_file))
            self._jobs_cache = jobs_data.get('jobs', {})
        except Exception:
            self._jobs_cache = {}

        try:
            tasks_data = asyncio.run(load_file(self.tasks_file))
            self._tasks_cache = {task['id']: task for task in tasks_data.get('tasks', {}).values()}
        except Exception:
            self._tasks_cache = {}

        try:
            users_data = asyncio.run(load_file(self.users_file))
            self._users_cache = users_data.get('users', {})
        except Exception:
            self._users_cache = {}

        try:
            wl_data = asyncio.run(load_file(self.whitelist_file))
            self._whitelist_cache = wl_data.get('whitelist', {})
        except Exception:
            self._whitelist_cache = {}

        try:
            sessions_data = asyncio.run(load_file(self.sessions_file))
            self._sessions_cache = sessions_data.get('sessions', {})
        except Exception:
            self._sessions_cache = {}

        try:
            history_data = asyncio.run(load_file(self.history_file))
            self._history_cache = history_data.get('history', {})
        except Exception:
            self._history_cache = {}

        try:
            ss_data = asyncio.run(load_file(self.session_state_file))
            self._session_state_cache = ss_data.get('session_state', {})
        except Exception:
            self._session_state_cache = {}

    # ... Implement methods similarly to previous FileStorageBackend (omitted for brevity)
    # The full implementations are in the existing `db/storage.py` now; this file serves as modular backend.
    async def _save_jobs(self):
        import json
        import aiofiles
        try:
            backup_data = {"jobs": self._jobs_cache, "timestamp": str(datetime.now())}
            async with aiofiles.open(self.jobs_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save jobs: {e}")

    async def _save_tasks(self):
        import json
        import aiofiles
        try:
            backup_data = {"tasks": self._tasks_cache, "timestamp": str(datetime.now())}
            async with aiofiles.open(self.tasks_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")

    async def _save_users(self):
        import json
        import aiofiles
        try:
            backup_data = {"users": self._users_cache, "timestamp": str(datetime.now())}
            async with aiofiles.open(self.users_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save users: {e}")

    async def _save_whitelist(self):
        import json
        import aiofiles
        try:
            backup_data = {"whitelist": self._whitelist_cache, "timestamp": str(datetime.now())}
            async with aiofiles.open(self.whitelist_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save whitelist: {e}")

    async def _save_sessions(self):
        import json
        import aiofiles
        try:
            backup_data = {"sessions": self._sessions_cache, "timestamp": str(datetime.now())}
            async with aiofiles.open(self.sessions_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save sessions: {e}")

    async def _save_history(self):
        import json
        import aiofiles
        try:
            backup_data = {"history": self._history_cache, "timestamp": str(datetime.now())}
            async with aiofiles.open(self.history_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")

    async def _save_session_state(self):
        import json
        import aiofiles
        try:
            backup_data = {"session_state": self._session_state_cache, "timestamp": str(datetime.now())}
            async with aiofiles.open(self.session_state_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save session state: {e}")

    async def store_job(self, job_data: Dict[str, Any]) -> bool:
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
        return self._jobs_cache.get(job_id)

    async def get_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        jobs = list(self._jobs_cache.values())
        if status:
            jobs = [job for job in jobs if job.get('status') == status]
        return jobs

    async def update_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
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
        return self._tasks_cache.get(task_id)

    async def get_tasks(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        tasks = list(self._tasks_cache.values())
        if is_active is not None:
            tasks = [task for task in tasks if task.get('is_active') == is_active]
        return tasks

    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
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
        return {
            "jobs": self._jobs_cache,
            "tasks": self._tasks_cache,
            "users": self._users_cache,
            "whitelist": self._whitelist_cache,
            "sessions": self._sessions_cache,
            "history": self._history_cache,
            "session_state": self._session_state_cache,
            "timestamp": str(datetime.now()),
            "total_jobs": len(self._jobs_cache),
            "total_tasks": len(self._tasks_cache),
        }

    async def restore_data(self, backup_data: Dict[str, Any]) -> bool:
        try:
            self._jobs_cache = backup_data.get('jobs', {})
            self._tasks_cache = {task['id']: task for task in backup_data.get('tasks', {}).values()}
            self._users_cache = backup_data.get('users', {})
            self._whitelist_cache = backup_data.get('whitelist', {})
            self._sessions_cache = backup_data.get('sessions', {})
            self._history_cache = backup_data.get('history', {})
            self._session_state_cache = backup_data.get('session_state', {})

            await self._save_jobs()
            await self._save_tasks()
            await self._save_users()
            await self._save_whitelist()
            await self._save_sessions()
            await self._save_history()
            await self._save_session_state()

            return True
        except Exception as e:
            self.logger.error(f"Failed to restore data: {e}")
            return False

    # User & Whitelist implementations
    async def store_user(self, user_data: Dict[str, Any]) -> bool:
        try:
            uid = user_data.get('internal_user_id')
            if not uid:
                return False
            self._users_cache[uid] = user_data
            await self._save_users()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store user: {e}")
            return False

    async def get_user(self, internal_user_id: str) -> Optional[Dict[str, Any]]:
        return self._users_cache.get(internal_user_id)

    async def get_users(self) -> List[Dict[str, Any]]:
        return list(self._users_cache.values())

    async def update_user(self, internal_user_id: str, user_data: Dict[str, Any]) -> bool:
        try:
            if internal_user_id in self._users_cache:
                self._users_cache[internal_user_id].update(user_data)
                await self._save_users()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update user: {e}")
            return False

    async def delete_user(self, internal_user_id: str) -> bool:
        try:
            if internal_user_id in self._users_cache:
                del self._users_cache[internal_user_id]
                await self._save_users()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete user: {e}")
            return False

    async def store_whitelist(self, whitelist_data: Dict[str, Any]) -> bool:
        try:
            wid = whitelist_data.get('whitelist_id')
            if not wid:
                return False
            self._whitelist_cache[wid] = whitelist_data
            await self._save_whitelist()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store whitelist: {e}")
            return False

    async def get_whitelist(self, whitelist_id: str) -> Optional[Dict[str, Any]]:
        return self._whitelist_cache.get(whitelist_id)

    async def get_whitelist_by_platform(self, platform: str, platform_user_id: str) -> Optional[Dict[str, Any]]:
        for w in self._whitelist_cache.values():
            if w.get('platform') == platform and w.get('platform_user_id') == platform_user_id:
                return w
        return None

    async def update_whitelist(self, whitelist_id: str, whitelist_data: Dict[str, Any]) -> bool:
        try:
            if whitelist_id in self._whitelist_cache:
                self._whitelist_cache[whitelist_id].update(whitelist_data)
                await self._save_whitelist()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update whitelist: {e}")
            return False

    async def delete_whitelist(self, whitelist_id: str) -> bool:
        try:
            if whitelist_id in self._whitelist_cache:
                del self._whitelist_cache[whitelist_id]
                await self._save_whitelist()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete whitelist: {e}")
            return False

    # Sessions & History
    async def store_session(self, session_data: Dict[str, Any]) -> bool:
        try:
            sid = session_data.get('session_id')
            if not sid:
                return False
            self._sessions_cache[sid] = session_data
            await self._save_sessions()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store session: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions_cache.get(session_id)

    async def get_sessions(self, internal_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        sessions = list(self._sessions_cache.values())
        if internal_user_id:
            sessions = [s for s in sessions if s.get('internal_user_id') == internal_user_id]
        return sessions

    async def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        try:
            if session_id in self._sessions_cache:
                self._sessions_cache[session_id].update(session_data)
                await self._save_sessions()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update session: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        try:
            if session_id in self._sessions_cache:
                del self._sessions_cache[session_id]
                await self._save_sessions()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete session: {e}")
            return False

    async def store_history(self, history_data: Dict[str, Any]) -> bool:
        try:
            iid = history_data.get('interaction_id')
            if not iid:
                return False
            self._history_cache[iid] = history_data
            await self._save_history()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store history: {e}")
            return False

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return [h for h in self._history_cache.values() if h.get('session_id') == session_id]

    async def get_recent_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        hist = await self.get_history(session_id)
        try:
            hist_sorted = sorted(hist, key=lambda x: x.get('timestamp') or '', reverse=True)
        except Exception:
            hist_sorted = hist
        return hist_sorted[:limit]

    async def delete_history(self, interaction_id: str) -> bool:
        try:
            if interaction_id in self._history_cache:
                del self._history_cache[interaction_id]
                await self._save_history()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete history: {e}")
            return False

    # Session state
    async def store_session_state(self, state_data: Dict[str, Any]) -> bool:
        try:
            sid = state_data.get('session_id')
            if not sid:
                return False
            self._session_state_cache[sid] = state_data
            await self._save_session_state()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store session state: {e}")
            return False

    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._session_state_cache.get(session_id)

    async def update_session_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        try:
            if session_id in self._session_state_cache:
                self._session_state_cache[session_id].update(state_data)
                await self._save_session_state()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update session state: {e}")
            return False

    async def delete_session_state(self, session_id: str) -> bool:
        try:
            if session_id in self._session_state_cache:
                del self._session_state_cache[session_id]
                await self._save_session_state()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete session state: {e}")
            return False
