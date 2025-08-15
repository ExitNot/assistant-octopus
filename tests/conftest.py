#!/usr/bin/env python3
"""
Pytest configuration and fixtures for the test suite.

This file provides common fixtures and configuration that can be used
across all test modules in the project.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the project root to the path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def mock_image_api_response():
    """Provide a mock successful image API response."""
    return {
        "data": [
            {
                "url": "https://example.com/generated_image.jpg",
                "b64_json": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            }
        ],
        "created": 1234567890,
        "model": "dall-e-3"
    }


@pytest.fixture(scope="session")
def mock_image_api_error_response():
    """Provide a mock error image API response."""
    return {
        "error": {
            "message": "The request was rejected as a result of our safety system",
            "type": "invalid_request_error",
            "code": "content_policy_violation"
        }
    }


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Automatically mock environment variables for all tests."""
    with patch.dict(os.environ, {
        'IMAGE_ROUTER_API_KEY': 'test_api_key_12345'
    }):
        yield


@pytest.fixture(autouse=True)
def mock_logging():
    """Automatically mock logging to avoid output during tests."""
    with patch('services.image.image_service.logging') as mock_logging:
        yield mock_logging