from utils.constants import CHROMA, IMG_TEST, INF_YOU, SDXL
from ..image_model import ImageGenModel, ImageGenerationProviderClient, ImageGenerationResult, ResponseFormat
from utils.config import get_settings
import logging
import requests


settings = get_settings()
logger = logging.getLogger(__name__)

class ImageRouterProvider(ImageGenerationProviderClient):
    """
    Provider for interacting with the ImageRouter API for AI-powered image generation.
    
    This class handles authentication, request formatting, and response processing
    for the ImageRouter service. It supports various image generation parameters
    and can return results in different formats.
    
    Attributes:
        api_url: The base URL for the ImageRouter API
        api_key: Authentication key for API access
        headers: HTTP headers including authorization and content type
    """
    api_key: str
    headers: dict


    def __init__(self, api_url: str):
        models = [
            ImageGenModel(nickname="Chroma", name=CHROMA, quality_options=None),
            ImageGenModel(nickname="SDXL", name=SDXL, quality_options=None),
            ImageGenModel(nickname="InfiniteYou", name=INF_YOU, quality_options=None),
            ImageGenModel(nickname="Test", name=IMG_TEST, quality_options=None)
        ]
        name = "ImageRouterProvider"
        super().__init__(name, api_url, models)

        self.api_key = settings.image_router_api_key
        self.headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

    def generate(self, model: str, prompt: str, settings: dict) -> ImageGenerationResult:
        """
        Generate an image using the ImageRouter API.
        
        Args:
            prompt: Text description of the image to generate
            model: AI model to use for generation (e.g., "Chroma", "SDXL")
            response_format: Desired output format (URL or BASE64), defaults to URL
            size: Image dimensions (e.g., "1024x1024"), optional
            quality: Image quality (e.g., "auto", "low", "medium", "high"), optional
            
        Returns:
            ImageGenerationResult: Object containing the generated image data and metadata
        """

        model_name = self.get_model_data(model).name 
        payload = {
            "model": model_name,
            "prompt": prompt,
        }
        
        # Add optional parameters if provided
        opt_size = settings.get('size')
        opt_quality = settings.get('quality')
        opt_response_format = settings.get('response_format')
        if opt_size:
            payload['size'] = opt_size
        if opt_quality:
            payload['quality'] = opt_quality
        if opt_response_format:
            payload['response_format'] = opt_response_format
        
        logger.info(f"ImageRouter API Request: (payload:{payload})")
            
        error_message = None
        image_data = None
        result_json = None
        
        try:
            # Make the API request
            logger.info("Making HTTP POST request to ImageRouter API...")
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            
            logger.info(f"HTTP Response received:")
            logger.info(f"  Status Code: {response.status_code}")
            logger.info(f"  Headers: {dict(response.headers)}")
            
            result_json = response.json()
            logger.debug(f"ImageRouter API Response: {result_json}")
            
            # Error handling
            if 'error' in result_json:
                error_info = result_json['error']
                error_message = error_info.get('message', 'Unknown API error')
                error_type = error_info.get('type', 'unknown')
                
                logger.error(f"API returned error: {error_type} - {error_message}")
                
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
                    size=opt_size,
                    quality=opt_quality,
                    response_format=ResponseFormat(opt_response_format) if opt_response_format else ResponseFormat.URL,
                    result=result_json,
                    error=error_message
                )
            
            # Taking result
            image_data = None
            
            # OpenAI-compatible format with 'data' array
            if 'data' in result_json and result_json['data']:
                if isinstance(result_json['data'], list) and len(result_json['data']) > 0:
                    resp_fmt_enum = ResponseFormat(opt_response_format) if opt_response_format else ResponseFormat.URL
                    if resp_fmt_enum == ResponseFormat.URL:
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
        
        logger.info(f"ImageRouterClient.generate() result: \
                        Success: {image_data is not None} \
                        Image Data: {image_data[:100] if image_data else 'None'}... \
                        Error: {error_message}")
        
        return ImageGenerationResult(
            data=image_data,
            prompt=prompt,
            model=model,
            size=opt_size,
            quality=opt_quality,
            response_format=ResponseFormat(opt_response_format) if opt_response_format else ResponseFormat.URL,
            result=result_json,
            error=error_message
        )

    def get_model_data(self, model_nick: str) -> ImageGenModel:
        for model in self.models:
            if model.nickname == model_nick:
                return model
        return ValueError("Not found")