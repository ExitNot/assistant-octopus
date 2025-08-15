#!/usr/bin/env python3
"""
Tests for Image Generation Tool

This module contains tests for the ImageGenerationTool class,
including unit tests with mocked dependencies.

Dependencies:
    - pytest: For test framework
    - unittest.mock: For mocking external dependencies
    - services.image.image_generation_tool: The tool being tested
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.image.image_generation_tool import ImageGenerationTool


class TestImageGenerationTool:
    """Test cases for ImageGenerationTool class."""
    
    @pytest.fixture
    def mock_image_service(self):
        """Provide a mock ImageService for testing."""
        return Mock()
    
    @pytest.fixture
    def image_generation_tool(self, mock_image_service):
        """Create an ImageGenerationTool instance with mocked dependencies."""
        with patch('services.image.image_generation_tool.ImageService') as mock_service_class:
            mock_service_class.return_value = mock_image_service
            
            tool = ImageGenerationTool()
            tool.image_service = mock_image_service
            return tool
    
    def test_initialization(self, image_generation_tool):
        """Test tool initialization."""
        assert image_generation_tool is not None
        assert hasattr(image_generation_tool, 'image_service')
    
    def test_get_available_models(self, image_generation_tool, mock_image_service):
        """Test getting available models."""
        expected_models = ['model1', 'model2', 'model3']
        mock_image_service.get_supported_models.return_value = expected_models
        
        models = image_generation_tool.get_available_models()
        
        assert models == expected_models
        mock_image_service.get_supported_models.assert_called_once()
    
    def test_get_available_sizes(self, image_generation_tool, mock_image_service):
        """Test getting available sizes."""
        expected_sizes = ['256x256', '1024x1024']
        mock_image_service.get_supported_sizes.return_value = expected_sizes
        
        sizes = image_generation_tool.get_available_sizes()
        
        assert sizes == expected_sizes
        mock_image_service.get_supported_sizes.assert_called_once()
    
    def test_get_available_qualities(self, image_generation_tool, mock_image_service):
        """Test getting available qualities."""
        expected_qualities = ['low', 'medium', 'high']
        mock_image_service.get_supported_qualities.return_value = expected_qualities
        
        qualities = image_generation_tool.get_available_qualities()
        
        assert qualities == expected_qualities
        mock_image_service.get_supported_qualities.assert_called_once()
    
    def test_generate_image_empty_prompt(self, image_generation_tool):
        """Test image generation with empty prompt."""
        result = image_generation_tool.generate_image("")
        
        assert result["success"] is False
        assert "Prompt cannot be empty" in result["error"]
    
    def test_generate_image_short_prompt(self, image_generation_tool):
        """Test image generation with short prompt."""
        result = image_generation_tool.generate_image("short")
        
        assert result["success"] is False
        assert "too short" in result["error"]
    
    def test_generate_image_long_prompt(self, image_generation_tool):
        """Test image generation with long prompt."""
        long_prompt = "a" * 1001
        result = image_generation_tool.generate_image(long_prompt)
        
        assert result["success"] is False
        assert "too long" in result["error"]
    
    def test_generate_image_invalid_model(self, image_generation_tool, mock_image_service):
        """Test image generation with invalid model."""
        mock_image_service.get_supported_models.return_value = ['valid_model']
        
        result = image_generation_tool.generate_image(
            "A beautiful sunset", 
            model="invalid_model"
        )
        
        assert result["success"] is False
        assert "Invalid model" in result["error"]
    
    def test_generate_image_invalid_size(self, image_generation_tool, mock_image_service):
        """Test image generation with invalid size."""
        mock_image_service.get_supported_sizes.return_value = ['1024x1024']
        
        result = image_generation_tool.generate_image(
            "A beautiful sunset", 
            size="invalid_size"
        )
        
        assert result["success"] is False
        assert "Invalid size" in result["error"]
    
    def test_generate_image_invalid_quality(self, image_generation_tool, mock_image_service):
        """Test image generation with invalid quality."""
        mock_image_service.get_supported_qualities.return_value = ['high']
        
        result = image_generation_tool.generate_image(
            "A beautiful sunset", 
            quality="invalid_quality"
        )
        
        assert result["success"] is False
        assert "Invalid quality" in result["error"]
    
    def test_generate_image_success(self, image_generation_tool, mock_image_service):
        """Test successful image generation."""
        # Mock successful result
        mock_result = Mock()
        mock_result.is_successful.return_value = True
        mock_result.data = "https://example.com/image.jpg"
        mock_result.model = "test_model"
        mock_result.size = "1024x1024"
        mock_result.quality = "high"
        mock_result.prompt = "A beautiful sunset"
        
        mock_image_service.generate_image.return_value = mock_result
        
        result = image_generation_tool.generate_image("A beautiful sunset")
        
        assert result["success"] is True
        assert result["data"] == "https://example.com/image.jpg"
        assert result["model"] == "test_model"
        assert result["size"] == "1024x1024"
        assert result["quality"] == "high"
        assert result["prompt"] == "A beautiful sunset"
    
    def test_generate_image_failure(self, image_generation_tool, mock_image_service):
        """Test failed image generation."""
        # Mock failed result
        mock_result = Mock()
        mock_result.is_successful.return_value = False
        mock_result.error = "API error occurred"
        
        mock_image_service.generate_image.return_value = mock_result
        
        result = image_generation_tool.generate_image("A beautiful sunset")
        
        assert result["success"] is False
        assert "API error occurred" in result["error"]
    
    def test_get_tool_description(self, image_generation_tool):
        """Test getting tool description."""
        description = image_generation_tool.get_tool_description()
        
        assert "Image Generation Tool" in description
        assert "generate images" in description.lower()
        assert "Available Models" in description
        assert "Available Sizes" in description
        assert "Available Qualities" in description
    
    def test_get_tool_schema(self, image_generation_tool, mock_image_service):
        """Test getting tool schema."""
        mock_image_service.get_supported_models.return_value = ['model1', 'model2']
        mock_image_service.get_supported_sizes.return_value = ['256x256', '1024x1024']
        mock_image_service.get_supported_qualities.return_value = ['low', 'high']
        
        schema = image_generation_tool.get_tool_schema()
        
        assert schema["name"] == "image_generation_tool"
        assert schema["description"] == "Generate images based on text descriptions"
        assert "prompt" in schema["parameters"]["properties"]
        assert "model" in schema["parameters"]["properties"]
        assert "size" in schema["parameters"]["properties"]
        assert "quality" in schema["parameters"]["properties"]
        assert "prompt" in schema["parameters"]["required"]
