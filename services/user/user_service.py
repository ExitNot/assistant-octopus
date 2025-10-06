"""
User Management Service implementation.
Provides user CRUD, platform binding management, and user lookup.
Aligns with ADR-03 and project coding standards.
"""
from typing import Optional, Dict, Any, List
from db.storage import get_storage_backend
from models.user_models import UserEntity
from utils.logger import get_logger

logger = get_logger(__name__)


import asyncio
backend = get_storage_backend()


async def create_user(*, user: UserEntity) -> Optional[UserEntity]:
    try:
        result = await backend.users.create(user.to_dict())
        return UserEntity.from_dict(result) if result else None
    except Exception as exc:
        logger.error(f"Failed to create user: {exc}")
        return None

async def get_user(*, internal_user_id: str) -> Optional[UserEntity]:
    try:
        result = await backend.users.get(internal_user_id)
        return UserEntity.from_dict(result) if result else None
    except Exception as exc:
        logger.error(f"Failed to get user {internal_user_id}: {exc}")
        return None

async def list_users() -> List[UserEntity]:
    try:
        results = await backend.users.list()
        return [UserEntity.from_dict(u) for u in results]
    except Exception as exc:
        logger.error(f"Failed to list users: {exc}")
        return []

async def update_user(*, internal_user_id: str, user_update: Dict[str, Any]) -> Optional[UserEntity]:
    try:
        result = await backend.users.update(internal_user_id, user_update)
        return UserEntity.from_dict(result) if result else None
    except Exception as exc:
        logger.error(f"Failed to update user {internal_user_id}: {exc}")
        return None

async def delete_user(*, internal_user_id: str) -> bool:
    try:
        return await backend.users.delete(internal_user_id)
    except Exception as exc:
        logger.error(f"Failed to delete user {internal_user_id}: {exc}")
        return False

async def add_platform_binding(*, internal_user_id: str, platform: str, platform_user_id: str) -> Optional[UserEntity]:
    user = await get_user(internal_user_id=internal_user_id)
    if not user:
        return None
    user.platform_bindings[platform] = platform_user_id
    return await update_user(internal_user_id=internal_user_id, user_update={"platform_bindings": user.platform_bindings})

async def remove_platform_binding(*, internal_user_id: str, platform: str) -> Optional[UserEntity]:
    user = await get_user(internal_user_id=internal_user_id)
    if not user or platform not in user.platform_bindings:
        return None
    user.platform_bindings.pop(platform)
    return await update_user(internal_user_id=internal_user_id, user_update={"platform_bindings": user.platform_bindings})

async def lookup_user_by_platform(*, platform: str, platform_user_id: str) -> Optional[UserEntity]:
    users = await list_users()
    for user in users:
        if user.platform_bindings.get(platform) == platform_user_id:
            return user
    return None
