from pydantic_settings import BaseSettings
from pydantic import Field, AnyUrl, ValidationError
from typing import Optional
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    ollama_api_url: AnyUrl = Field(..., env="OLLAMA_API_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except ValidationError as e:
            raise RuntimeError(f"Configuration error: {e}")
    return _settings 