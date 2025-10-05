from typing import List, Optional
from db.storage import StorageBackend
from models.user_models import ConversationHistoryEntity


class HistoryRepo:
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def list(self, session_id: str) -> List[ConversationHistoryEntity]:
        data = await self.storage.history.list(session_id=session_id)
        return [ConversationHistoryEntity.from_dict(d) for d in data]

    async def recent(self, session_id: str, limit: int = 20) -> List[ConversationHistoryEntity]:
        # Supabase backend implements history.list; if a recent() optimized query exists, backend may expose it.
        data = await self.storage.history.list(session_id=session_id)
        return [ConversationHistoryEntity.from_dict(d) for d in data[:limit]]

    async def create(self, history: ConversationHistoryEntity) -> ConversationHistoryEntity:
        result = await self.storage.history.create(history.to_dict())
        if not result:
            raise RuntimeError("Failed to store history entry")
        if isinstance(result, dict):
            return ConversationHistoryEntity.from_dict(result)
        return history

    async def delete(self, interaction_id: str) -> bool:
        return await self.storage.history.delete(interaction_id)
