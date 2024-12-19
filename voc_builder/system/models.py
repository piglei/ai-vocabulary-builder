from dataclasses import dataclass
from typing import Optional


@dataclass
class OpenAIConfig:
    """The configuration of OpenAI service."""

    api_key: str
    api_host: str
    model: str


@dataclass
class GeminiConfig:
    """The configuration of Gemini service."""

    api_key: str
    api_host: str
    model: str


@dataclass
class AnthropicConfig:
    """The configuration of Anthropic service."""

    api_key: str
    api_host: str
    model: str


@dataclass
class SystemSettings:
    """The system settings for the project.

    target_language: the target language.
    """

    model_provider: str
    openai_config: OpenAIConfig
    gemini_config: GeminiConfig

    anthropic_config: Optional[AnthropicConfig] = None
    target_language: str = ""

    def __post_init__(self):
        if self.anthropic_config is None:
            self.anthropic_config = AnthropicConfig(api_key="", api_host="", model="")


def build_default_settings() -> SystemSettings:
    """Build the default system settings, all fields are using the default value."""
    return SystemSettings(
        model_provider="",
        openai_config=OpenAIConfig(api_key="", api_host="", model=""),
        gemini_config=GeminiConfig(api_key="", api_host="", model=""),
        anthropic_config=AnthropicConfig(api_key="", api_host="", model=""),
    )
