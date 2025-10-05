from typing import Optional, List
from db.storage import StorageBackend
from models.user_models import WhitelistEntity


class WhitelistRepo:
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def get(self, whitelist_id: str) -> Optional[WhitelistEntity]:
        if not whitelist_id:
            return None
        data = await self.storage.whitelist.get(whitelist_id)
        if not data:
            return None
        return WhitelistEntity.from_dict(data)

    async def get_by_platform(self, platform: str, platform_user_id: str) -> Optional[WhitelistEntity]:
        data = await self.storage.whitelist.list(platform=platform, platform_user_id=platform_user_id)
        if not data:
            return None
        # list() returns a list; return the first matching item
        return WhitelistEntity.from_dict(data[0])

    async def create(self, whitelist: WhitelistEntity) -> WhitelistEntity:
        result = await self.storage.whitelist.create(whitelist.to_dict())
        if not result:
            raise RuntimeError("Failed to create whitelist entry")
        if isinstance(result, dict):
            return WhitelistEntity.from_dict(result)
        return whitelist

    async def update(self, whitelist_id: str, whitelist: WhitelistEntity) -> bool:
        updated = await self.storage.whitelist.update(whitelist_id, whitelist.to_dict())
        return updated is not None

    async def delete(self, whitelist_id: str) -> bool:
        return await self.storage.whitelist.delete(whitelist_id)
