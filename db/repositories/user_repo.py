from typing import Optional, List
from db.storage import StorageBackend
from models.user_models import UserEntity


class UserRepo:
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def get(self, internal_user_id: str) -> Optional[UserEntity]:
        if not internal_user_id:
            return None
        data = await self.storage.users.get(internal_user_id)
        if not data:
            return None
        return UserEntity.from_dict(data)

    async def create(self, user: UserEntity) -> UserEntity:
        result = await self.storage.users.create(user.to_dict())
        if not result:
            raise RuntimeError(f"Failed to create user {user.internal_user_id}")
        # If backend returns the created row, convert it; otherwise return the input entity
        if isinstance(result, dict):
            return UserEntity.from_dict(result)
        return user

    async def list(self) -> List[UserEntity]:
        data = await self.storage.users.list()
        return [UserEntity.from_dict(d) for d in data]

    async def update(self, internal_user_id: str, user: UserEntity) -> bool:
        updated = await self.storage.users.update(internal_user_id, user.to_dict())
        return updated is not None

    async def delete(self, internal_user_id: str) -> bool:
        return await self.storage.users.delete(internal_user_id)
