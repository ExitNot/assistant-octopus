#!/usr/bin/env python3
"""
Tests for Image Service Module

This module contains comprehensive tests for the ImageService class,
including unit tests with mocked API calls and integration test scenarios.

Dependencies:
    - pytest: For test framework
    - unittest.mock: For mocking external dependencies
    - services.image.image_service: The service being tested
    - services.image.image_generator: For result classes
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.image.image_service import ImageService
from services.image.image_generator import ImageGenerationResult, ResponseFormat


class TestImageService:
    """Test cases for ImageService class."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Provide a mock API key for testing."""
        return "test_api_key_12345"
    
    @pytest.fixture
    def mock_base_url(self):
        """Provide a mock base URL for testing."""
        return "https://api.test.com/v1/images"
    
    @pytest.fixture
    def image_service(self, mock_api_key, mock_base_url):
        """Create an ImageService instance with mocked dependencies."""
        with patch('services.image.image_service.ImageRouterClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            service = ImageService(api_key=mock_api_key, base_url=mock_base_url)
            service.client = mock_client
            return service
    
    @pytest.fixture
    def successful_image_result(self):
        """Provide a mock successful image generation result."""
        return ImageGenerationResult(
            data="https://example.com/generated_image.jpg",
            prompt="A beautiful sunset over mountains",
            model="dall-e-3",
            size="1024x1024",
            quality="standard",
            response_format=ResponseFormat.URL,
            result={"data": [{"url": "https://example.com/generated_image.jpg"}]},
            error=None
        )
    
    @pytest.fixture
    def failed_image_result(self):
        """Provide a mock failed image generation result."""
        return ImageGenerationResult(
            data=None,
            prompt="Invalid prompt",
            model="dall-e-3",
            size="1024x1024",
            quality="standard",
            response_format=ResponseFormat.URL,
            result=None,
            error="API request failed"
        )
    
    def test_image_service_initialization(self, mock_api_key, mock_base_url):
        """Test ImageService initialization."""
        with patch('services.image.image_service.ImageRouterClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            service = ImageService(api_key=mock_api_key, base_url=mock_base_url)
            
            assert service.client == mock_client
            assert service.default_model == "dall-e-3"
            assert service.default_size == "1024x1024"
            assert service.default_quality == "standard"
    
    def test_generate_image_success(self, image_service, successful_image_result):
        """Test successful image generation."""
        # Mock the client's generate method
        image_service.client.generate.return_value = successful_image_result
        
        result = image_service.generate_image(
            prompt="A beautiful sunset over mountains",
            model="dall-e-3",
            size="1024x1024"
        )
        
        # Verify the result
        assert result.is_successful() is True
        assert result.data == "https://example.com/generated_image.jpg"
        assert result.prompt == "A beautiful sunset over mountains"
        assert result.model == "dall-e-3"
        assert result.size == "1024x1024"
        
        # Verify the client was called correctly
        image_service.client.generate.assert_called_once_with(
            prompt="A beautiful sunset over mountains",
            model="dall-e-3",
            response_format=ResponseFormat.URL,
            size="1024x1024",
            quality="standard"
        )
    
    def test_generate_image_with_defaults(self, image_service, successful_image_result):
        """Test image generation using service defaults."""
        image_service.client.generate.return_value = successful_image_result
        
        result = image_service.generate_image(prompt="A cat")
        
        # Verify defaults were used
        image_service.client.generate.assert_called_once_with(
            prompt="A cat",
            model="dall-e-3",
            response_format=ResponseFormat.URL,
            size="1024x1024",
            quality="standard"
        )
    
    def test_generate_image_empty_prompt(self, image_service):
        """Test image generation with empty prompt."""
        result = image_service.generate_image(prompt="")
        
        assert result.is_successful() is False
        assert result.error == "Prompt cannot be empty"
        assert result.data is None
        
        # Verify client was not called
        image_service.client.generate.assert_not_called()
    
    def test_generate_image_whitespace_prompt(self, image_service):
        """Test image generation with whitespace-only prompt."""
        result = image_service.generate_image(prompt="   ")
        
        assert result.is_successful() is False
        assert result.error == "Prompt cannot be empty"
        assert result.data is None
        
        # Verify client was not called
        image_service.client.generate.assert_not_called()
    
    def test_generate_image_failure(self, image_service, failed_image_result):
        """Test failed image generation."""
        image_service.client.generate.return_value = failed_image_result
        
        result = image_service.generate_image(prompt="Invalid prompt")
        
        assert result.is_successful() is False
        assert result.error == "API request failed"
        assert result.data is None
    
    def test_generate_image_base64_format(self, image_service):
        """Test image generation with BASE64 response format."""
        base64_result = ImageGenerationResult(
            data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            prompt="A simple test image",
            model="dall-e-3",
            size="1024x1024",
            quality="standard",
            response_format=ResponseFormat.BASE64,
            result={"data": [{"b64_json": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="}]},
            error=None
        )
        
        image_service.client.generate.return_value = base64_result
        
        result = image_service.generate_image(
            prompt="A simple test image",
            response_format=ResponseFormat.BASE64
        )
        
        assert result.is_successful() is True
        assert result.response_format == ResponseFormat.BASE64
        assert result.data.startswith("iVBOR")
        
        # Verify the correct format was passed to client
        image_service.client.generate.assert_called_once_with(
            prompt="A simple test image",
            model="dall-e-3",
            response_format=ResponseFormat.BASE64,
            size="1024x1024",
            quality="standard"
        )
    
    def test_generate_image_batch_success(self, image_service):
        """Test successful batch image generation."""
        prompts = ["A cat", "A dog", "A bird"]
        successful_results = []
        
        for prompt in prompts:
            result = ImageGenerationResult(
                data=f"https://example.com/{prompt.lower()}.jpg",
                prompt=prompt,
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                response_format=ResponseFormat.URL,
                result={"data": [{"url": f"https://example.com/{prompt.lower()}.jpg"}]},
                error=None
            )
            successful_results.append(result)
        
        # Mock the client to return different results for each call
        image_service.client.generate.side_effect = successful_results
        
        results = image_service.generate_image_batch(prompts)
        
        assert len(results) == 3
        assert all(result.is_successful() for result in results)
        assert results[0].data == "https://example.com/a cat.jpg"
        assert results[1].data == "https://example.com/a dog.jpg"
        assert results[2].data == "https://example.com/a bird.jpg"
        
        # Verify client was called for each prompt
        assert image_service.client.generate.call_count == 3
    
    def test_generate_image_batch_empty_list(self, image_service):
        """Test batch generation with empty prompts list."""
        results = image_service.generate_image_batch([])
        
        assert results == []
        image_service.client.generate.assert_not_called()
    
    def test_generate_image_batch_partial_failure(self, image_service):
        """Test batch generation with some failures."""
        prompts = ["A cat", "Invalid prompt", "A bird"]
        
        # Mock mixed results: success, failure, success
        mixed_results = [
            ImageGenerationResult(
                data="https://example.com/cat.jpg",
                prompt="A cat",
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                response_format=ResponseFormat.URL,
                result={"data": [{"url": "https://example.com/cat.jpg"}]},
                error=None
            ),
            ImageGenerationResult(
                data=None,
                prompt="Invalid prompt",
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                response_format=ResponseFormat.URL,
                result=None,
                error="API request failed"
            ),
            ImageGenerationResult(
                data="https://example.com/bird.jpg",
                prompt="A bird",
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                response_format=ResponseFormat.URL,
                result={"data": [{"url": "https://example.com/bird.jpg"}]},
                error=None
            )
        ]
        
        image_service.client.generate.side_effect = mixed_results
        
        results = image_service.generate_image_batch(prompts)
        
        assert len(results) == 3
        assert results[0].is_successful() is True
        assert results[1].is_successful() is False
        assert results[2].is_successful() is True
    
    def test_validate_prompt_valid(self, image_service):
        """Test prompt validation with valid input."""
        validation = image_service._validate_prompt("A beautiful landscape with mountains and trees")
        
        assert validation["is_valid"] is True
        assert validation["issues"] == []
        assert validation["word_count"] == 7
    
    def test_validate_prompt_empty(self, image_service):
        """Test prompt validation with empty input."""
        validation = image_service._validate_prompt("")
        
        assert validation["is_valid"] is False
        assert "Prompt is empty" in validation["issues"]
        assert validation["word_count"] == 0
    
    def test_validate_prompt_too_short(self, image_service):
        """Test prompt validation with too short input."""
        validation = image_service._validate_prompt("Cat")
        
        assert validation["is_valid"] is False
        assert "Prompt is too short (minimum 10 characters)" in validation["issues"]
        assert "Add more descriptive details to your prompt" in validation["suggestions"]
        assert validation["word_count"] == 1
    
    def test_validate_prompt_too_long(self, image_service):
        """Test prompt validation with too long input."""
        long_prompt = "A " + "very " * 200 + "long prompt"
        validation = image_service._validate_prompt(long_prompt)
        
        assert validation["is_valid"] is False
        assert "Prompt is too long (maximum 1000 characters)" in validation["issues"]
        assert "Consider breaking into multiple, focused prompts" in validation["suggestions"]
    
    def test_validate_prompt_inappropriate_content(self, image_service):
        """Test prompt validation with inappropriate content."""
        validation = image_service._validate_prompt("A nude portrait")
        
        assert validation["is_valid"] is True
        assert validation["issues"] == []
    


class TestImageServiceIntegration:
    """Integration tests for ImageService with mocked external dependencies."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'IMAGE_ROUTER_API_KEY': 'test_key_12345'
        }):
            yield
    
    def test_service_with_real_constants(self, mock_env_vars):
        """Test service initialization with real constants import."""
        with patch('services.image.image_service.ImageRouterClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # This should work without errors
            service = ImageService(api_key="test_key")
            
            assert service.client == mock_client
            assert service.default_model == "dall-e-3"
    
    def test_service_error_handling(self, mock_env_vars):
        """Test service error handling with various failure scenarios."""
        with patch('services.image.image_service.ImageRouterClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            service = ImageService(api_key="test_key")
            
            # Test with None prompt
            result = service.generate_image(prompt=None)
            assert result.is_successful() is False
            assert "Prompt cannot be empty" in result.error
            
            # Test with very long prompt - mock a proper ImageGenerationResult
            from services.image.image_generator import ImageGenerationResult
            long_prompt = "A " + "very " * 300 + "long prompt"
            mock_result = ImageGenerationResult(
                data="https://example.com/test.jpg",
                prompt=long_prompt,  # Use the actual long prompt
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                response_format=ResponseFormat.URL,
                result={"data": [{"url": "https://example.com/test.jpg"}]},
                error=None
            )
            mock_client.generate.return_value = mock_result
            
            result = service.generate_image(prompt=long_prompt)
            # Should work since validation is separate from generation
            assert result.prompt == long_prompt


if __name__ == "__main__":
    pytest.main([__file__])
