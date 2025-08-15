from pydantic_settings import BaseSettings
from pydantic import Field, AnyUrl, ValidationError
from typing import Optional
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    ollama_api_url: AnyUrl = Field(..., env="OLLAMA_API_URL")
    telegram_bot_token: str = Field(..., env="TELERGRAM_BOT_TOKEN")
    supervisor_api_url: AnyUrl = Field(..., env="SUPERVISOR_API_URL")
    
    # Messaging Service Configuration
    messaging_backup_file: str = Field(default="jobs_backup.json", env="MESSAGING_BACKUP_FILE")
    messaging_max_retries: int = Field(default=3, env="MESSAGING_MAX_RETRIES")
    messaging_backup_interval: int = Field(default=60, env="MESSAGING_BACKUP_INTERVAL")
    
    # Job Queue Configuration
    job_queue_priority_enabled: bool = Field(default=True, env="JOB_QUEUE_PRIORITY_ENABLED")

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