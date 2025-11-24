"""Pydantic schema for application configuration loaded from config.json."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class ProviderModels(BaseModel):
    """Model identifiers for a provider."""

    research_model: str = Field(...)
    final_report_model: str = Field(...)
    compression_model: str = Field(...)
    summarization_model: str = Field(...)


class ProviderConfig(BaseModel):
    """Configuration for a single model provider (e.g., openai, anthropic)."""

    display_name: str = Field(...)
    description: Optional[str] = Field(default=None)
    api_key_env: str = Field(...)
    models: ProviderModels = Field(...)


class ResearchDefaults(BaseModel):
    """Default values for deep research configuration in the UI."""

    max_iterations: int = Field(1)
    max_tool_calls: int = Field(3)
    allow_clarification: bool = Field(False)
    max_concurrent: int = Field(2)
    timeout_minutes: int = Field(15)
    # Accept values such as "anthropic", "openai", "tavily", "none"
    search_api: str = Field("anthropic")


class AppConfig(BaseModel):
    """Root application configuration mapping providers and defaults."""

    default_provider: str = Field(...)
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    research_defaults: ResearchDefaults = Field(default_factory=ResearchDefaults)


