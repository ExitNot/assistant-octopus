#!/usr/bin/env python3
"""
Image Generation Tool for Agent

This module provides a tool interface for the agent to generate images
using the ImageService. It handles validation, error handling, and
provides a clean interface for the agent to use.

Dependencies:
    - services.image.image_service: For image generation functionality
    - typing: For type hints
    - logging: For service logging
"""

import logging
from typing import Optional, Dict, Any
from services.image.image_service import ImageService
from utils.config import get_settings
from utils.constants import IMAGE_API

logger = logging.getLogger(__name__)
settings = get_settings()

class ImageGenerationTool:
    """
    Tool for generating images that can be used by the agent.
    
    This tool provides a clean interface for the agent to generate images
    with proper validation and error handling.
    """
    
    def __init__(self):
        """Initialize the ImageGenerationTool."""
        self.image_service = ImageService(
            api_key=settings.image_router_api_key,
            base_url=IMAGE_API
        )
        logger.info("ImageGenerationTool initialized successfully")
    
    def get_available_models(self) -> list[str]:
        """
        Get list of available image generation models.
        
        Returns:
            List of available model names
        """
        return self.image_service.get_supported_models()
    
    def get_model_constraints(self) -> Dict[str, Dict[str, Any]]:
        """
        Get constraints for each model (quality, size limitations, etc.).
        
        Returns:
            Dictionary mapping model names to their constraints
        """
        return {
            "stabilityai/sdxl-turbo:free": {
                "qualities": ["low", "medium"],
                "sizes": ["256x256", "512x512", "1024x1024"],
                "note": "Free model - limited quality options"
            },
            "ByteDance/InfiniteYou:free": {
                "qualities": ["auto", "low", "medium", "high"],
                "sizes": ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"],
                "note": "Free model - full feature set"
            },
            "lodestones/Chroma:free": {
                "qualities": ["auto", "low", "medium", "high"],
                "sizes": ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"],
                "note": "Free model - full feature set"
            },
            "test/test": {
                "qualities": ["auto", "low", "medium", "high"],
                "sizes": ["256x256", "512x512", "1024x1024"],
                "note": "Test model - for development only"
            }
        }
    
    def validate_model_parameters(self, model: str, quality: Optional[str] = None, size: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that the requested parameters are compatible with the selected model.
        
        Args:
            model: The model to validate against
            quality: The requested quality
            size: The requested size
            
        Returns:
            Dictionary with validation result and suggestions
        """
        constraints = self.get_model_constraints().get(model, {})
        
        if not constraints:
            return {
                "valid": False,
                "error": f"Unknown model: {model}",
                "suggestions": []
            }
        
        issues = []
        suggestions = []
        
        # Validate quality
        if quality and quality not in constraints.get("qualities", []):
            issues.append(f"Quality '{quality}' not supported by model '{model}'")
            suggestions.append(f"Use one of: {', '.join(constraints['qualities'])}")
        
        # Validate size
        if size and size not in constraints.get("sizes", []):
            issues.append(f"Size '{size}' not supported by model '{model}'")
            suggestions.append(f"Use one of: {', '.join(constraints['sizes'])}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "constraints": constraints
        }
    
    def get_available_sizes(self) -> list[str]:
        """
        Get list of available image sizes.
        
        Returns:
            List of available size formats
        """
        return self.image_service.get_supported_sizes()
    
    def get_available_qualities(self) -> list[str]:
        """
        Get list of available image qualities.
        
        Returns:
            List of available quality settings
        """
        return self.image_service.get_supported_qualities()
    
    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        size: Optional[str] = None,
        quality: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an image using the specified parameters.
        
        Args:
            prompt: Text description of the image to generate
            model: AI model to use (optional, uses default if not specified)
            size: Image dimensions (optional, uses default if not specified)
            quality: Image quality (optional, uses default if not specified)
            
        Returns:
            Dictionary containing the result of the image generation
        """
        # Log the incoming request
        logger.info(f"Image generation request received:")
        logger.info(f"  Prompt: '{prompt}'")
        logger.info(f"  Model: {model or 'default'}")
        logger.info(f"  Size: {size or 'default'}")
        logger.info(f"  Quality: {quality or 'default'}")
        
        # Input validation
        if not prompt or not prompt.strip():
            logger.warning("Empty prompt provided")
            return {
                "success": False,
                "error": "Prompt cannot be empty",
                "data": None
            }
        
        if len(prompt.strip()) < 10:
            logger.warning(f"Prompt too short: {len(prompt.strip())} characters (minimum 10)")
            return {
                "success": False,
                "error": "Prompt is too short (minimum 10 characters). Please provide more details.",
                "data": None
            }
        
        if len(prompt.strip()) > 1000:
            logger.warning(f"Prompt too long: {len(prompt.strip())} characters (maximum 1000)")
            return {
                "success": False,
                "error": "Prompt is too long (maximum 1000 characters). Please provide a shorter description.",
                "data": None
            }
        
        # Validate model if provided
        if model:
            available_models = self.get_available_models()
            logger.info(f"Validating model '{model}' against available models: {available_models}")
            
            if model not in available_models:
                logger.error(f"Invalid model '{model}' requested")
                return {
                    "success": False,
                    "error": f"Invalid model '{model}'. Available models: {', '.join(available_models)}",
                    "data": None
                }
            
            # Validate model-specific constraints
            logger.info(f"Validating model constraints for '{model}'")
            validation = self.validate_model_parameters(model, quality, size)
            if not validation["valid"]:
                logger.warning(f"Model constraint validation failed for '{model}': {validation['issues']}")
                error_msg = "Model parameter validation failed:\n"
                for issue in validation["issues"]:
                    error_msg += f"• {issue}\n"
                if validation["suggestions"]:
                    error_msg += "\nSuggestions:\n"
                    for suggestion in validation["suggestions"]:
                        error_msg += f"• {suggestion}\n"
                
                return {
                    "success": False,
                    "error": error_msg.strip(),
                    "data": None,
                    "constraints": validation["constraints"]
                }
            else:
                logger.info(f"Model constraint validation passed for '{model}'")
        
        # Validate size if provided
        if size:
            available_sizes = self.get_available_sizes()
            logger.info(f"Validating size '{size}' against available sizes: {available_sizes}")
            
            if size not in available_sizes:
                logger.error(f"Invalid size '{size}' requested")
                return {
                    "success": False,
                    "error": f"Invalid size '{size}'. Available sizes: {', '.join(available_sizes)}",
                    "data": None
                }
        
        # Validate quality if provided
        if quality:
            available_qualities = self.get_available_qualities()
            logger.info(f"Validating quality '{quality}' against available qualities: {available_qualities}")
            
            if quality not in available_qualities:
                logger.error(f"Invalid quality '{quality}' requested")
                return {
                    "success": False,
                    "error": f"Invalid quality '{quality}'. Available qualities: {', '.join(available_qualities)}",
                    "data": None
                }
        
        # Log final parameters being sent to the service
        final_model = model or "default"
        final_size = size or "default"
        final_quality = quality or "default"
        
        logger.info(f"Calling ImageService with parameters:")
        logger.info(f"  Final Prompt: '{prompt.strip()}'")
        logger.info(f"  Final Model: {final_model}")
        logger.info(f"  Final Size: {final_size}")
        logger.info(f"  Final Quality: {final_quality}")
        
        try:
            # Generate the image
            logger.info("Making API call to ImageService...")
            result = self.image_service.generate_image(
                prompt=prompt.strip(),
                model=model,
                size=size,
                quality=quality
            )
            
            logger.info(f"ImageService response received:")
            logger.info(f"  Success: {result.is_successful()}")
            logger.info(f"  Has Data: {result.data is not None}")
            logger.info(f"  Error: {result.error}")
            logger.info(f"  Model Used: {result.model}")
            logger.info(f"  Size Used: {result.size}")
            logger.info(f"  Quality Used: {result.quality}")
            
            if result.is_successful() and result.data:
                logger.info("✅ Image generation successful!")
                return {
                    "success": True,
                    "data": result.data,
                    "model": result.model,
                    "size": result.size,
                    "quality": result.quality,
                    "prompt": result.prompt,
                    "message": "Image generated successfully"
                }
            else:
                # Add debugging information
                error_details = result.error or "Unknown error occurred during image generation"
                logger.error(f"Image generation failed: {error_details}")
                
                if result.result:
                    logger.debug(f"Raw API Response: {result.result}")
                    error_details += f" (API Response: {result.result})"
                
                return {
                    "success": False,
                    "error": error_details,
                    "data": None,
                    "debug_info": {
                        "api_response": result.result,
                        "model_used": result.model,
                        "size_used": result.size,
                        "quality_used": result.quality
                    }
                }
                
        except Exception as e:
            logger.error(f"Exception during image generation: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"An error occurred while generating the image: {str(e)}",
                "data": None
            }
    
    def debug_api_response(self, prompt: str, model: Optional[str] = None, size: Optional[str] = None, quality: Optional[str] = None) -> Dict[str, Any]:
        """
        Debug method to test API calls and see the raw response structure.
        
        This method is useful for troubleshooting API response format issues.
        
        Args:
            prompt: Text description of the image to generate
            model: AI model to use (optional)
            size: Image dimensions (optional)
            quality: Image quality (optional)
            
        Returns:
            Dictionary containing debug information about the API call
        """
        try:
            # Make a test call to see the raw API response
            result = self.image_service.generate_image(
                prompt=prompt.strip(),
                model=model,
                size=size,
                quality=quality
            )
            
            return {
                "success": result.is_successful(),
                "raw_response": result.result,
                "error": result.error,
                "extracted_data": result.data,
                "model_used": result.model,
                "size_used": result.size,
                "quality_used": result.quality,
                "prompt_used": result.prompt
            }
            
        except Exception as e:
            logger.error(f"Error during debug API call: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_response": None,
                "extracted_data": None
            }
    
    def get_tool_description(self) -> str:
        """
        Get a description of this tool for the agent.
        
        Returns:
            String description of the tool and its capabilities
        """
        return """Image Generation Tool

This tool allows you to generate images based on text descriptions.

Usage:
- Use this tool when a user requests image generation
- Provide a detailed prompt describing what you want to generate
- Optionally specify model, size, and quality parameters

Available Models:
- sdxl: Fast generation, good quality
- inf: InfiniteYou model
- chroma: Chroma model
- test: Test model

Available Sizes:
- 256x256, 512x512, 1024x1024
- 1792x1024, 1024x1792

Available Qualities:
- auto, low, medium, high

Example: Generate an image of a beautiful sunset over mountains using the sdxl model at 1024x1024 resolution with high quality."""
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """
        Get the tool schema for the agent.
        
        Returns:
            Dictionary containing the tool schema
        """
        return {
            "name": "image_generation_tool",
            "description": "Generate images based on text descriptions",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Detailed description of the image to generate (10-1000 characters)",
                        "minLength": 10,
                        "maxLength": 1000
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use for generation",
                        "enum": self.get_available_models()
                    },
                    "size": {
                        "type": "string",
                        "description": "Image dimensions",
                        "enum": self.get_available_sizes()
                    },
                    "quality": {
                        "type": "string",
                        "description": "Image quality setting",
                        "enum": self.get_available_qualities()
                    }
                },
                "required": ["prompt"]
            }
        }

# Create a global instance for easy access
image_generation_tool = ImageGenerationTool()
