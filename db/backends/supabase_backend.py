from typing import Optional, Dict, Any, List
from db.backends.base import StorageBackend, JobStore, TaskStore, UserStore, WhitelistStore, SessionStore, HistoryStore, SessionStateStore
from utils.config import get_settings
from utils.logger import get_logger
from db.supabase_client import get_supabase_client


class _JobStore(JobStore):
    def __init__(self, client):
        self.client = client

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.insert_job(data)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.client.get_job(id)

    async def list(self, **filters) -> List[Dict[str, Any]]:
        return await self.client.get_jobs(status=filters.get('status'))

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.update_job(id, data)

    async def delete(self, id: str) -> bool:
        return await self.client.delete_job(id)


class _TaskStore(TaskStore):
    def __init__(self, client):
        self.client = client

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.insert_task(data)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.client.get_task(id)

    async def list(self, **filters) -> List[Dict[str, Any]]:
        return await self.client.get_tasks(is_active=filters.get('is_active'))

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.update_task(id, data)

    async def delete(self, id: str) -> bool:
        return await self.client.delete_task(id)


class _UserStore(UserStore):
    def __init__(self, client):
        self.client = client

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.insert_user(data)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.client.get_user(id)

    async def list(self, **filters) -> List[Dict[str, Any]]:
        return await self.client.get_users()

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.update_user(id, data)

    async def delete(self, id: str) -> bool:
        return await self.client.delete_user(id)


class _WhitelistStore(WhitelistStore):
    def __init__(self, client):
        self.client = client

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.insert_whitelist(data)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.client.get_whitelist(id)

    async def list(self, **filters) -> List[Dict[str, Any]]:
        # No generic list implemented; return single-item list if platform filter provided
        if 'platform' in filters and 'platform_user_id' in filters:
            item = await self.client.get_whitelist_by_platform(filters['platform'], filters['platform_user_id'])
            return [item] if item else []
        return []

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.update_whitelist(id, data)

    async def delete(self, id: str) -> bool:
        return await self.client.delete_whitelist(id)


class _SessionStore(SessionStore):
    def __init__(self, client):
        self.client = client

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.insert_session(data)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.client.get_session(id)

    async def list(self, **filters) -> List[Dict[str, Any]]:
        return await self.client.get_sessions(internal_user_id=filters.get('internal_user_id'))

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.update_session(id, data)

    async def delete(self, id: str) -> bool:
        return await self.client.delete_session(id)


class _HistoryStore(HistoryStore):
    def __init__(self, client):
        self.client = client

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.insert_history(data)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        # Not used; history queried by session_id
        return None

    async def list(self, **filters) -> List[Dict[str, Any]]:
        return await self.client.get_history(filters.get('session_id'))

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # not supported
        return None

    async def delete(self, id: str) -> bool:
        return await self.client.delete_history(id)


class _SessionStateStore(SessionStateStore):
    def __init__(self, client):
        self.client = client

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.insert_session_state(data)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.client.get_session_state(id)

    async def list(self, **filters) -> List[Dict[str, Any]]:
        return []

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.client.update_session_state(id, data)

    async def delete(self, id: str) -> bool:
        return await self.client.delete_session_state(id)


class SupabaseStorageBackend(StorageBackend):
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.client = get_supabase_client()

        # instantiate per-entity stores
        self._jobs = _JobStore(self.client)
        self._tasks = _TaskStore(self.client)
        self._users = _UserStore(self.client)
        self._whitelist = _WhitelistStore(self.client)
        self._sessions = _SessionStore(self.client)
        self._history = _HistoryStore(self.client)
        self._session_state = _SessionStateStore(self.client)

    @property
    def jobs(self) -> JobStore:
        return self._jobs

    @property
    def tasks(self) -> TaskStore:
        return self._tasks

    @property
    def users(self) -> UserStore:
        return self._users

    @property
    def whitelist(self) -> WhitelistStore:
        return self._whitelist

    @property
    def sessions(self) -> SessionStore:
        return self._sessions

    @property
    def history(self) -> HistoryStore:
        return self._history

    @property
    def session_state(self) -> SessionStateStore:
        return self._session_state

