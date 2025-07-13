import os
import pytest
import conftest
from httpx import AsyncClient, ASGITransport
from services.api import app

import pytest_asyncio

@pytest.mark.asyncio
async def test_supervisor_execute():
    payload = {"prompt": "Hello, assistant!", "session_id": "testsession", "user_id": "testuser"}
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/supervisor/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["session_id"] == "testsession"
    assert data["user_id"] == "testuser" 