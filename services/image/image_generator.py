#!/usr/bin/env python3 
"""
Image Generator Module

This module provides functionality for generating images using the ImageRouter API.
It includes classes for handling image generation requests, managing API responses,
and formatting results in different output formats (URL or Base64).

Dependencies:
    - requests: For making HTTP requests to the ImageRouter API
    - dotenv: For loading environment variables
    - utils.constants: For API endpoint configuration
"""

from enum import Enum
from typing import Optional
import requests
import os
from utils.constants import IMAGE_API
import logging

logger = logging.getLogger(__name__)


class ResponseFormat(Enum):
    """
    Enumeration for image response formats supported by the ImageRouter API.
    
    Attributes:
        URL: Return image as a downloadable URL
        BASE64: Return image as base64 encoded JSON string
    """
    URL = "url"
    BASE64 = "b64_json"


class ImageGenerationResult:
    """
    Data class representing the result of an image generation request.
    
    Attributes:
        data: The generated image URL (for URL format) or base64 data (for BASE64 format)
        prompt: The text prompt used to generate the image
        model: The AI model used for image generation
        size: The dimensions of the generated image (e.g., "1024x1024")
        quality: The quality setting used for generation (e.g., "standard", "hd")
        response_format: The format of the response (URL or BASE64)
        result: The raw API response data
        error: Error message if the request fails (None if successful)
    """
    data: Optional[str]
    prompt: str
    model: str
    size: Optional[str]
    quality: Optional[str]
    response_format: ResponseFormat
    result: Optional[dict]
    error: Optional[str]

    def __init__(self, data: Optional[str], prompt: str, model: str, size: Optional[str], quality: Optional[str], response_format: ResponseFormat, result: Optional[dict], error: Optional[str] = None):
        """
        Initialize an ImageGenerationResult instance.
        
        Args:
            data: The generated image URL or base64 data (None if error occurred)
            prompt: The text prompt used for generation
            model: The AI model used
            size: Image dimensions (optional)
            quality: Image quality setting (optional)
            response_format: Response format enum value
            result: Raw API response data (None if error occurred)
            error: Error message if the request fails
        """
        self.data = data
        self.prompt = prompt
        self.model = model
        self.size = size
        self.quality = quality
        self.response_format = response_format
        self.result = result
        self.error = error

    def is_successful(self) -> bool:
        """
        Check if the image generation was successful.
        
        Returns:
            bool: True if successful, False if an error occurred
        """
        return self.error is None


class ImageRouterClient:
    """
    Client for interacting with the ImageRouter API for AI-powered image generation.
    
    This class handles authentication, request formatting, and response processing
    for the ImageRouter service. It supports various image generation parameters
    and can return results in different formats.
    
    Attributes:
        url: The base URL for the ImageRouter API
        api_key: Authentication key for API access
        headers: HTTP headers including authorization and content type
    """
    url: str
    api_key: str
    headers: dict

    def __init__(self, url: str, api_key: str):
        """
        Initialize the ImageRouter client.
        
        Args:
            url: Base URL for the ImageRouter API
            api_key: API key for authentication
        """
        self.url = url
        self.api_key = api_key
        # Set up authentication and content type headers
        self.headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        }

    def generate(self, prompt: str, model: str, response_format: Optional[ResponseFormat] = ResponseFormat.URL, size: Optional[str] = None, quality: Optional[str] = None):
        """
        Generate an image using the ImageRouter API.
        
        Args:
            prompt: Text description of the image to generate
            model: AI model to use for generation (e.g., "dall-e-3", "midjourney")
            response_format: Desired output format (URL or BASE64), defaults to URL
            size: Image dimensions (e.g., "1024x1024"), optional
            quality: Image quality (e.g., "auto", "low", "medium", "high"), optional
            
        Returns:
            ImageGenerationResult: Object containing the generated image data and metadata
        """
        # Build the request payload with required and optional parameters
        payload = {
            "model": model,
            "prompt": prompt,
        }
        
        # Add optional parameters if provided
        if size: 
            payload['size'] = size
        if quality: 
            payload['quality'] = quality
        if response_format: 
            payload['response_format'] = response_format.value
        
        logger.info(f"ImageRouter API Request:")
        logger.info(f"  URL: {self.url}")
        logger.info(f"  Model: {model}")
        logger.info(f"  Prompt: '{prompt[:50]}...'")
        logger.info(f"  Size: {size or 'not specified'}")
        logger.info(f"  Quality: {quality or 'not specified'}")
        logger.info(f"  Response Format: {response_format.value}")
        logger.info(f"  Full Payload: {payload}")
        logger.info(f"  Headers: {self.headers}")
            
        error_message = None
        image_data = None
        result_json = None
        
        try:
            # Make the API request
            logger.info("Making HTTP POST request to ImageRouter API...")
            response = requests.post(self.url, json=payload, headers=self.headers)
            
            logger.info(f"HTTP Response received:")
            logger.info(f"  Status Code: {response.status_code}")
            logger.info(f"  Headers: {dict(response.headers)}")
            
            # Check if response contains an error
            result_json = response.json()
            logger.debug(f"ImageRouter API Response: {result_json}")
            
            # Check for API errors first
            if 'error' in result_json:
                error_info = result_json['error']
                error_message = error_info.get('message', 'Unknown API error')
                error_type = error_info.get('type', 'unknown')
                
                logger.error(f"API returned error: {error_type} - {error_message}")
                
                # Handle specific error types
                if 'insufficient credits' in error_message.lower():
                    error_message = f"Insufficient credits: {error_message}. Please top up your ImageRouter account at https://imagerouter.io/pricing"
                elif 'bad request' in error_message.lower():
                    error_message = f"Invalid request: {error_message}"
                elif 'unauthorized' in error_message.lower() or 'authentication' in error_message.lower():
                    error_message = f"Authentication error: {error_message}. Please check your API key."
                
                return ImageGenerationResult(
                    data=None,
                    prompt=prompt,
                    model=model,
                    size=size,
                    quality=quality,
                    response_format=response_format,
                    result=result_json,
                    error=error_message
                )
            
            # If no error, try to extract image data
            image_data = None
            
            # OpenAI-compatible format with 'data' array
            if 'data' in result_json and result_json['data']:
                if isinstance(result_json['data'], list) and len(result_json['data']) > 0:
                    if response_format == ResponseFormat.URL:
                        image_data = result_json['data'][0].get('url')
                    else:
                        image_data = result_json['data'][0].get('b64_json')
            
            # Direct URL in response
            elif 'url' in result_json:
                image_data = result_json['url']
            
            if not image_data:
                error_message = f"Could not extract image data from API response. Response structure: {result_json}"
                logger.error(f"Failed to extract image data from response: {result_json}")
            else:
                logger.info(f"Successfully extracted image data: {image_data[:100]}...")
                
        except requests.exceptions.RequestException as e:
            error_message = f"Request failed: {str(e)}"
            logger.error(f"HTTP request failed: {e}")
        except (KeyError, IndexError, ValueError) as e:
            error_message = f"Response parsing error: {str(e)}"
            logger.error(f"Response parsing failed: {e}, Response: {result_json}")
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error during image generation: {e}")
        
        # Log the final result
        logger.info(f"ImageRouterClient.generate() result:")
        logger.info(f"  Success: {image_data is not None}")
        logger.info(f"  Image Data: {image_data[:100] if image_data else 'None'}...")
        logger.info(f"  Error: {error_message}")
        
        return ImageGenerationResult(
            data=image_data,
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            response_format=response_format,
            result=result_json,
            error=error_message
        )
