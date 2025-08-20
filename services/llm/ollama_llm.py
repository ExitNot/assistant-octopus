import httpx
from typing import AsyncGenerator, Optional, Dict, Any, Union
from enum import Enum
from utils.config import get_settings
from openai import OpenAI

class OllamaModel(str, Enum):
    GEMMA = "gemma3:4b"
    LLAMA3_2 = "llama3.2:1b" # Default
    LLAMA3_2_Q4 = "llama3.2:3b-q4_0" # 3B model with 4-bit quantization

class OllamaAPIError(Exception):
    pass

class OllamaClient:
    api_url: str

    def __init__(self, api_url: Optional[str] = None):
        settings = get_settings()
        self.api_url = api_url or str(settings.ollama_api_url)

    async def generate(
        self,
        prompt: str,
        model: OllamaModel = OllamaModel.LLAMA3_2,
        messages: list[dict] = [],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate text from Ollama API.
        If stream=True, returns an async generator yielding response chunks.
        If stream=False, returns the full response as a string.
        """
        client = OpenAI(base_url=self.api_url, api_key='ollama')
        headers = {"Accept": "application/json"}
        payload = {"model": model.value, "prompt": prompt, "stream": stream}
        if options:
            payload["options"] = options
        try:
            result = client.chat.completions.create(
                model = model,
                messages = messages,
                stream = stream
            )
        except httpx.HTTPError as e:
            raise OllamaAPIError(f"Ollama API request failed: {e}") from e
        if stream:
            async def stream_gen():
                async for line in result.aiter_lines():
                    if line.strip():
                        yield line
            return stream_gen()

        response = result.choices[0].message.content

        if not response:
            raise OllamaAPIError(f"Unexpected Ollama API response: {response}, result: {result}")
        return response