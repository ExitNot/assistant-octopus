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
from .image_model import ImageGenerationProvider, ImageGenerationProviderClient, ImageGenerationResult, ResponseFormat
from .providers.image_router_provider import ImageRouterProvider
from .providers.together_ai_provider import TogetherAiProvider
from utils.constants import IMAGE_API, TOGETHER_AI_API

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
    
    provider: ImageGenerationProviderClient

    def __init__(self, provider: ImageGenerationProvider = ImageGenerationProvider.IMG_ROUTER):
        """
        Initialize the ImageService.
        
        Args:
            api_key: API key for ImageRouter authentication
            base_url: Base URL for the ImageRouter API (optional)
        """
        self.provider = self._get_provider_client(provider)

        logger.info("ImageService initialized successfully")
    
    def generate_image(
        self,
        prompt: str,
        model: str,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        response_format: ResponseFormat = ResponseFormat.URL
    ) -> ImageGenerationResult:
        """
        Generate an image using the specified parameters.
        
        Args:
            prompt: Text description of the image to generate
            model: AI model to use
            size: Image dimensions (Optional)
            quality: Image quality (Optional)
            response_format: Output format (URL or BASE64)
            
        Returns:
            ImageGenerationResult: Result object with image data and metadata
        """
        # Log the incoming request
        logger.info(f"ImageService.generate_image called with: (model:{model}, size:{size}, quality:{quality}, response_format:{response_format})")
        
        # Validate input parameters
        if not prompt or not prompt.strip():
            logger.error("Empty or invalid prompt provided")
            return ImageGenerationResult(
                prompt=prompt or "",
                model=model,
                size=size,
                quality=quality,
                response_format=response_format,
                result=None,
                error="Prompt cannot be empty"
            )
        
        available_models = self.provider.models
        if model not in [model.nickname for model in available_models]:
            logger.error(f"Model {model} is not available for this provider")
            return ImageGenerationResult(
                prompt=prompt or "",
                model=model,
                size=size,
                quality=quality,
                response_format=response_format,
                error="Model is not available for provider"
            )
        
        logger.info(f"Generating image with prompt: '{prompt[:50]}...'")
        logger.debug(f"Using model: {model}, size: {size}, quality: {quality}")
        
        # Generate the image
        logger.info("Calling ImageGenerationProviderClient.generate()...")
        settings = {}
        if size is not None: settings['size'] = size
        if quality is not None: settings['quality'] = quality
        if response_format: settings['response_format'] = response_format.value
        result = self.provider.generate(
            prompt=prompt.strip(),
            model=model,
            settings = settings
        )
        
        # Log the result
        logger.info(f"ImageRouterClient.generate() response: (Success: {result.is_successful()}, Has Data: {result.data is not None}, Error: {result.error})")
        
        if result.is_successful():
            logger.info("Image generation successful")
        else:
            logger.error(f"Image generation failed: {result.error}")
        
        return result
    
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
    
    def with_provider(self, provider_name: str):
        provider_client = self._get_provider_client(provider_name=provider_name)
        if provider_client is not None:
            self.provider = provider_client
        else:
            logger.error(f"Provider Client for {provider_name} was NotFond")
            raise ValueError(f"Provider Client for {provider_name} was NotFond")
        
        
    
    @staticmethod
    def get_supported_providers() -> list[ImageGenerationProvider]:
        return [
            ImageGenerationProvider.IMG_ROUTER,
            ImageGenerationProvider.TOGETHER_AI,
        ]


    def get_supported_models(self) -> list[str]:
        """
        Get list of supported AI models.
        
        Returns:
            List of supported model names
        """
        return [model.nickname for model in self.provider.models]
    
    def get_supported_sizes(self, model_nick: str) -> Optional[list[str]]:
        """
        Get list of supported image sizes.
        
        Returns:
            List of supported size formats
        """
        model = self.provider.get_model_data(model_nick)
        if model:
            return model.size_options
        return None
    
    def get_supported_qualities(self, model_nick) -> Optional[list[str]]:
        """
        Get list of supported image qualities.
        
        Returns:
            List of supported quality settings
        """
        model = self.provider.get_model_data(model_nick)
        if model:
            return model.quality_options
        return None
    
    @staticmethod
    def _get_provider_client(provider: Optional[ImageGenerationProvider] = None, provider_name: Optional[str] = None) -> Optional[ImageGenerationProviderClient]:
        if provider is ImageGenerationProvider.IMG_ROUTER or provider_name == ImageGenerationProvider.IMG_ROUTER.value:
            return ImageRouterProvider(api_url=IMAGE_API)
        elif provider is ImageGenerationProvider.TOGETHER_AI or provider_name == ImageGenerationProvider.TOGETHER_AI.value:
            return TogetherAiProvider(api_url=TOGETHER_AI_API)
        else:
            logger.debug(f"Image provider not found {provider} : provider_name: {provider_name}")
            return None
