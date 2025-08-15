#!/usr/bin/env python3
"""
Image Service Module

This module provides a high-level service interface for image generation,
abstracting the ImageRouter client and providing business logic for
image generation workflows.

Dependencies:
    - services.image.image_generator: For the ImageRouter client and result classes
    - typing: For type hints
    - logging: For service logging
"""

import logging
from typing import Optional, Dict, Any
from services.image.image_generator import (
    ImageRouterClient, 
    ImageGenerationResult, 
    ResponseFormat
)
from utils.constants import CHROMA, IMAGE_API, IMG_TEST, INF, SDXL

# Configure logging
logger = logging.getLogger(__name__)


class ImageService:
    """
    High-level service for image generation operations.
    
    This service provides business logic for image generation, including
    validation, error handling, and result processing. It acts as an
    abstraction layer above the ImageRouter client.
    
    Attributes:
        client: The ImageRouter client instance
        default_model: Default AI model to use for generation
        default_size: Default image size for generation
        default_quality: Default image quality setting
    """
    
    def __init__(self, api_key: str, base_url: str = IMAGE_API):
        """
        Initialize the ImageService.
        
        Args:
            api_key: API key for ImageRouter authentication
            base_url: Base URL for the ImageRouter API (optional)
        """
        
        self.client = ImageRouterClient(
            url=base_url,
            api_key=api_key
        )
        self.default_model = "dall-e-3"
        self.default_size = "1024x1024"
        self.default_quality = "standard"
        
        logger.info("ImageService initialized successfully")
    
    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        response_format: ResponseFormat = ResponseFormat.URL
    ) -> ImageGenerationResult:
        """
        Generate an image using the specified parameters.
        
        Args:
            prompt: Text description of the image to generate
            model: AI model to use (defaults to service default)
            size: Image dimensions (defaults to service default)
            quality: Image quality (defaults to service default)
            response_format: Output format (URL or BASE64)
            
        Returns:
            ImageGenerationResult: Result object with image data and metadata
        """
        # Log the incoming request
        logger.info(f"ImageService.generate_image called with:")
        logger.info(f"  Prompt: '{prompt}'")
        logger.info(f"  Model: {model or 'default'}")
        logger.info(f"  Size: {size or 'default'}")
        logger.info(f"  Quality: {quality or 'default'}")
        logger.info(f"  Response Format: {response_format}")
        
        # Validate input parameters
        if not prompt or not prompt.strip():
            logger.error("Empty or invalid prompt provided")
            return ImageGenerationResult(
                data=None,
                prompt=prompt or "",
                model=model or self.default_model,
                size=size or self.default_size,
                quality=quality or self.default_quality,
                response_format=response_format,
                result=None,
                error="Prompt cannot be empty"
            )
        
        # Use service defaults if not specified
        final_model = model or self.default_model
        final_size = size or self.default_size
        final_quality = quality or self.default_quality
        
        logger.info(f"Final parameters after applying defaults:")
        logger.info(f"  Final Model: {final_model}")
        logger.info(f"  Final Size: {final_size}")
        logger.info(f"  Final Quality: {final_quality}")
        logger.info(f"  Final Response Format: {response_format}")
        
        logger.info(f"Generating image with prompt: '{prompt[:50]}...'")
        logger.debug(f"Using model: {final_model}, size: {final_size}, quality: {final_quality}")
        
        # Generate the image
        logger.info("Calling ImageRouterClient.generate()...")
        result = self.client.generate(
            prompt=prompt.strip(),
            model=final_model,
            response_format=response_format,
            size=final_size,
            quality=final_quality
        )
        
        # Log the result
        logger.info(f"ImageRouterClient.generate() response:")
        logger.info(f"  Success: {result.is_successful()}")
        logger.info(f"  Has Data: {result.data is not None}")
        logger.info(f"  Error: {result.error}")
        logger.info(f"  Model: {result.model}")
        logger.info(f"  Size: {result.size}")
        logger.info(f"  Quality: {result.quality}")
        
        if result.is_successful():
            logger.info("Image generation successful in ImageService")
        else:
            logger.error(f"Image generation failed in ImageService: {result.error}")
        
        return result
    
    def generate_image_batch(
        self,
        prompts: list[str],
        model: Optional[str] = None,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        response_format: ResponseFormat = ResponseFormat.URL
    ) -> list[ImageGenerationResult]:
        """
        Generate multiple images from a list of prompts.
        
        Args:
            prompts: List of text descriptions for image generation
            model: AI model to use (defaults to service default)
            size: Image dimensions (defaults to service default)
            quality: Image quality (defaults to service default)
            response_format: Output format (URL or BASE64)
            
        Returns:
            List of ImageGenerationResult objects
        """
        if not prompts:
            logger.warning("Empty prompts list provided")
            return []
        
        logger.info(f"Generating batch of {len(prompts)} images")
        
        results = []
        for i, prompt in enumerate(prompts):
            logger.debug(f"Processing prompt {i+1}/{len(prompts)}")
            result = self.generate_image(
                prompt=prompt,
                model=model,
                size=size,
                quality=quality,
                response_format=response_format
            )
            results.append(result)
        
        successful_count = sum(1 for r in results if r.is_successful())
        logger.info(f"Batch generation complete: {successful_count}/{len(prompts)} successful")
        
        return results
    
    def _validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Validate a prompt for image generation.
        
        Args:
            prompt: Text prompt to validate
            
        Returns:
            Dictionary with validation results and suggestions
        """
        validation_result = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
            "word_count": 0
        }
        
        if not prompt or not prompt.strip():
            validation_result["is_valid"] = False
            validation_result["issues"].append("Prompt is empty")
            return validation_result
        
        # Count words
        words = prompt.strip().split()
        validation_result["word_count"] = len(words)
        
        # Check prompt length
        if len(prompt.strip()) < 10:
            validation_result["issues"].append("Prompt is too short (minimum 10 characters)")
            validation_result["suggestions"].append("Add more descriptive details to your prompt")
        
        if len(prompt.strip()) > 1000:
            validation_result["issues"].append("Prompt is too long (maximum 1000 characters)")
            validation_result["suggestions"].append("Consider breaking into multiple, focused prompts")
        
        # Update validity based on issues
        validation_result["is_valid"] = len(validation_result["issues"]) == 0
        
        return validation_result
    
    def get_supported_models(self) -> list[str]:
        """
        Get list of supported AI models.
        
        Returns:
            List of supported model names
        """
        return [
            SDXL,
            INF,
            CHROMA,
            IMG_TEST
        ]
    
    def get_supported_sizes(self) -> list[str]:
        """
        Get list of supported image sizes.
        
        Returns:
            List of supported size formats
        """
        return [
            "256x256",
            "512x512", 
            "1024x1024",
            "1792x1024",
            "1024x1792"
        ]
    
    def get_supported_qualities(self) -> list[str]:
        """
        Get list of supported image qualities.
        
        Returns:
            List of supported quality settings
        """
        return ['auto', 'low', 'medium', 'high']
