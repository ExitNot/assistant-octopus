"""
LLM Service Package

Handles communication with language models and AI services.
"""

from .ollama_llm import OllamaClient, OllamaAPIError, OllamaModel

__all__ = [
    "OllamaClient",
    "OllamaAPIError", 
    "OllamaModel"
]
