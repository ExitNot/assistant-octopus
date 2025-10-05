from typing import Optional, List
from db.storage import StorageBackend
from models.user_models import SessionEntity


class SessionRepo:
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def get(self, session_id: str) -> Optional[SessionEntity]:
        if not session_id:
            return None
        data = await self.storage.sessions.get(session_id)
        if not data:
            return None
        return SessionEntity.from_dict(data)

    async def list(self, internal_user_id: Optional[str] = None) -> List[SessionEntity]:
        data = await self.storage.sessions.list(internal_user_id=internal_user_id)
        return [SessionEntity.from_dict(d) for d in data]

    async def create(self, session: SessionEntity) -> SessionEntity:
        result = await self.storage.sessions.create(session.to_dict())
        if not result:
            raise RuntimeError("Failed to create session")
        if isinstance(result, dict):
            return SessionEntity.from_dict(result)
        return session

    async def update(self, session_id: str, session: SessionEntity) -> bool:
        updated = await self.storage.sessions.update(session_id, session.to_dict())
        return updated is not None

    async def delete(self, session_id: str) -> bool:
        return await self.storage.sessions.delete(session_id)
