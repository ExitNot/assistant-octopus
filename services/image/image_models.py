from typing import Optional
from abc import abstractmethod, ABC
from enum import Enum


DEFAULT_SIZE_OPTIONS = ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]

class ImageGenModel:
    nickname: str
    name: str
    size_options: Optional[list[str]]
    quality_options: Optional[list[str]]

    def __init__(self, nickname: str, name: str, quality_options: Optional[list[str]], size_options: Optional[list[str]] = DEFAULT_SIZE_OPTIONS):
        self.nickname = nickname
        self.name = name
        self.size_options = size_options
        self.quality_options = quality_options

    def is_quality_supported(self) -> bool:
        return self.quality_options is not None

    def is_size_supported(self) -> bool:
        return self.size_options is not None    

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

    def __init__(self, prompt: str, model: str, data: Optional[str] = None, size: Optional[str] = None, quality: Optional[str] = None, response_format: ResponseFormat = ResponseFormat.URL, result: Optional[dict] = None, error: Optional[str] = None):
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


class ImageGenerationProvider(Enum):
    IMG_ROUTER = "IMG_ROUTER"
    # OPEN_AI = "OpenAI"
    TOGETHER_AI = "TOGETHER_AI"


class ImageGenerationProviderClient(ABC):
    name: str
    api_url: str
    models: list[ImageGenModel]

    def __init__(self, name: str, api_url: str, models: list[ImageGenModel]):
        self.name = name
        self.api_url = api_url
        self.models = models

    @abstractmethod
    def generate(self, model: str, prompt: str, settings: dict) -> ImageGenerationResult:
        pass

    def get_model_data(self, model_nick: str) -> Optional[ImageGenModel]:
        for model in self.models:
            if model.nickname == model_nick:
                return model
        return None