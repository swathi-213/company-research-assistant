"""
Model Service for Deep Research Service 2.0
Handles model configuration and provider mapping
"""

from typing import Dict, Any, Optional
import logging
import json
import os
from pydantic import ValidationError
from .config_schema import AppConfig

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing AI model configurations and provider mappings"""
    
    def __init__(self):
        """Initialize the model service by loading configuration from config.json"""
        self._config = self._load_config()
        # Build a normalized mapping for quick access
        self.model_mappings: Dict[str, Dict[str, Any]] = {}
        for provider_key, provider in self._config.providers.items():
            self.model_mappings[provider_key] = {
                "research_model": provider.models.research_model,
                "final_report_model": provider.models.final_report_model,
                "compression_model": provider.models.compression_model,
                "summarization_model": provider.models.summarization_model,
                "provider": provider_key,
                "display_name": provider.display_name,
                "description": provider.description or "",
                "api_key_env": provider.api_key_env,
            }
        logger.debug("Model mappings initialized from config.json")

    def _load_config(self) -> AppConfig:
        """Load configuration from the root-level config.json using Pydantic validation."""
        # Workspace root is two levels up from this file
        
        project_root = os.curdir
        config_path = os.path.join(project_root, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return AppConfig(**raw)
        except FileNotFoundError:
            logger.error(f"Configuration file not found at {config_path}")
            raise
        except ValidationError as e:
            logger.error(f"Invalid configuration in config.json: {e}")
            raise
    
    def get_model_provider_mapping(self) -> Dict[str, str]:
        """
        Get model to provider mapping
        
        Returns:
            Dict mapping model names to their providers
        """
        return {provider: cfg["research_model"] for provider, cfg in self.model_mappings.items()}
    
    def get_model_config(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific model
        
        Args:
            model: Model identifier (openai, anthropic)
            
        Returns:
            Model configuration dict or None if not found
        """
        return self.model_mappings.get(model)
    
    def get_supported_models(self) -> list[str]:
        """
        Get list of supported models
        
        Returns:
            List of supported model identifiers
        """
        return list(self.model_mappings.keys())
    
    def validate_model(self, model: str) -> bool:
        """
        Validate if a model is supported
        
        Args:
            model: Model identifier to validate
            
        Returns:
            True if model is supported, False otherwise
        """
        return model in self.model_mappings
    
    def get_default_model(self) -> str:
        """
        Get the default model to use
        
        Returns:
            Default model identifier
        """
        return self._config.default_provider

    def get_research_defaults(self) -> Dict[str, Any]:
        """Return default deep research configuration from config.json."""
        rd = self._config.research_defaults
        return {
            "max_iterations": rd.max_iterations,
            "max_tool_calls": rd.max_tool_calls,
            "allow_clarification": rd.allow_clarification,
            "max_concurrent": rd.max_concurrent,
            "timeout_minutes": rd.timeout_minutes,
            "search_api": rd.search_api,
        }
    
    def get_model_display_name(self, model: str) -> str:
        """
        Get display name for a model
        
        Args:
            model: Model identifier
            
        Returns:
            Human-readable model name
        """
        config = self.model_mappings.get(model)
        if not config:
            return model
        return config.get("display_name", model)
    
    def get_model_description(self, model: str) -> str:
        """
        Get description for a model
        
        Args:
            model: Model identifier
            
        Returns:
            Model description
        """
        config = self.model_mappings.get(model)
        if not config:
            return "Unknown model"
        return config.get("description", "Unknown model")

    def get_required_api_key_env(self, model: str) -> Optional[str]:
        """Return the environment variable name that holds the API key for a given provider."""
        config = self.model_mappings.get(model)
        if not config:
            return None
        return config.get("api_key_env")