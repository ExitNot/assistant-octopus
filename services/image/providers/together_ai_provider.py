import logging
from services.image.image_models import ImageGenModel, ImageGenerationProviderClient, ImageGenerationResult
from utils.config import get_settings
from utils.constants import FLUX_FREE


settings = get_settings()
logger = logging.getLogger(__name__)

class TogetherAiProvider(ImageGenerationProviderClient):
    """
    Provider for interacting with the TogetherAi API for AI-powered image generation.
    
    This class handles requests formatting, and response processing
    for the TogetherAi API. It supports various image generation parameters
    and can return results in different formats.
    
    Attributes:
        url: The base URL for the TogetherAi API
        api_key: Authentication key for API access
    """
    api_key: str
    headers: dict


    def __init__(self, api_url: str):
        models = [
            ImageGenModel(nickname="FLUX", name=FLUX_FREE, quality_options=None)
        ]
        super().__init__("TogetherAiProvider", api_url, models)

        self.api_key = settings.image_router_api_key

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
        return False