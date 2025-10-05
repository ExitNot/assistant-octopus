from typing import Optional
from db.storage import StorageBackend
from models.user_models import SessionStateEntity


class SessionStateRepo:
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def get(self, session_id: str) -> Optional[SessionStateEntity]:
        data = await self.storage.session_state.get(session_id)
        if data is None:
            return None
        return SessionStateEntity.from_dict(data)

    async def create(self, state: SessionStateEntity) -> SessionStateEntity:
        result = await self.storage.session_state.create(state.to_dict())
        if not result:
            raise RuntimeError("Failed to store session state")
        if isinstance(result, dict):
            return SessionStateEntity.from_dict(result)
        return state

    async def update(self, session_id: str, state: SessionStateEntity) -> bool:
        updated = await self.storage.session_state.update(session_id, state.to_dict())
        return updated is not None

    async def delete(self, session_id: str) -> bool:
        return await self.storage.session_state.delete(session_id)
