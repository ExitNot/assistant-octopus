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
    image_router_api_key: str = Field(..., env="IMAGE_ROUTER_API_KEY")
    together_ai_api_key: str = Field(..., env="TOGETHER_AI_API_KEY")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="assistant_octopus", env="LOG_FILE")
    log_dir: str = Field(default="logs", env="LOG_DIR")
    log_max_bytes: int = Field(default=10 * 1024 * 1024, env="LOG_MAX_BYTES")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    log_console_output: bool = Field(default=True, env="LOG_CONSOLE_OUTPUT")
    
    # Messaging Service Configuration
    # TODO: Create corresponding .env variables
    # messaging_backup_file: str = Field(default="jobs_backup.json", env="MESSAGING_BACKUP_FILE")
    # messaging_max_retries: int = Field(default=3, env="MESSAGING_MAX_RETRIES")
    # messaging_backup_interval: int = Field(default=60, env="MESSAGING_BACKUP_INTERVAL")
    
    # Job Queue Configuration
    # job_queue_priority_enabled: bool = Field(default=True, env="JOB_QUEUE_PRIORITY_ENABLED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except ValidationError as e:
            raise RuntimeError(f"Configuration error: {e}")
    return _settings 