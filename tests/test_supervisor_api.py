import os
import pytest
import conftest
from httpx import AsyncClient, ASGITransport
from api.api import app
from unittest.mock import patch, AsyncMock
import pytest_asyncio

@pytest.mark.asyncio
async def test_supervisor_execute():
    """Test supervisor execute endpoint with mocked OllamaClient"""
    payload = {"prompt": "Hello, assistant!", "session_id": "testsession", "user_id": "testuser"}
    transport = ASGITransport(app=app)
    
    # Mock the OllamaClient.generate method to return a test response
    with patch('services.supervisor.supervisor_router.OllamaClient') as mock_ollama_class:
        mock_ollama_instance = AsyncMock()
        mock_ollama_instance.generate.return_value = "Hello! I'm your assistant. How can I help you today?"
        mock_ollama_class.return_value = mock_ollama_instance
        
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/supervisor/execute", json=payload)
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["session_id"] == "testsession"
        assert data["user_id"] == "testuser"
        assert data["response"] == "Hello! I'm your assistant. How can I help you today?"
        
        # Verify that OllamaClient was called correctly
        mock_ollama_instance.generate.assert_called_once()
        call_args = mock_ollama_instance.generate.call_args
        assert call_args[1]["prompt"] == "Hello, assistant!"
        assert call_args[1]["stream"] == False 