import pytest
import asyncio
from services.user import user_service
from models.user_models import UserEntity, AccessLevel, UserStatus
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_and_get_user():
    user = UserEntity(
        internal_user_id="test-user-id",
        platform_bindings={"telegram": "123456"},
        user_metadata={"nickname": "octotest"},
        access_level=AccessLevel.WHITELISTED,
        status=UserStatus.ACTIVE
    )
    with patch.object(user_service.backend.users, 'create', new=AsyncMock(return_value=user.to_dict())), \
         patch.object(user_service.backend.users, 'get', new=AsyncMock(return_value=user.to_dict())):
        created = await user_service.create_user(user=user)
        assert created is not None
        assert created.platform_bindings["telegram"] == "123456"
    assert created.internal_user_id is not None
    fetched = await user_service.get_user(internal_user_id=str(created.internal_user_id))
    assert fetched is not None
    assert fetched.internal_user_id == created.internal_user_id

@pytest.mark.asyncio
async def test_update_user():
    user = UserEntity(internal_user_id="test-user-id", platform_bindings={"telegram": "u1"})
    updated_dict = user.to_dict()
    updated_dict["user_metadata"] = {"nickname": "updated"}
    with patch.object(user_service.backend.users, 'update', new=AsyncMock(return_value=updated_dict)):
        assert user.internal_user_id is not None
        updated = await user_service.update_user(internal_user_id=str(user.internal_user_id), user_update={"user_metadata": {"nickname": "updated"}})
        assert updated is not None
        assert updated.user_metadata["nickname"] == "updated"

@pytest.mark.asyncio
async def test_delete_user():
    with patch.object(user_service.backend.users, 'delete', new=AsyncMock(return_value=True)):
        result = await user_service.delete_user(internal_user_id="fake-id")
        assert result is True

@pytest.mark.asyncio
async def test_platform_binding():
    user = UserEntity(internal_user_id="test-user-id", platform_bindings={})
    with patch.object(user_service, 'get_user', new=AsyncMock(return_value=user)), \
         patch.object(user_service, 'update_user', new=AsyncMock(return_value=user)):
        assert user.internal_user_id is not None
        added = await user_service.add_platform_binding(internal_user_id=str(user.internal_user_id), platform="telegram", platform_user_id="tgid")
        assert added is not None
        removed = await user_service.remove_platform_binding(internal_user_id=str(user.internal_user_id), platform="telegram")
        assert removed is not None

@pytest.mark.asyncio
async def test_lookup_user_by_platform():
    user = UserEntity(internal_user_id="test-user-id", platform_bindings={"telegram": "tgid"})
    with patch.object(user_service, 'list_users', new=AsyncMock(return_value=[user])):
        found = await user_service.lookup_user_by_platform(platform="telegram", platform_user_id="tgid")
        assert found is not None
        assert found.platform_bindings["telegram"] == "tgid"
