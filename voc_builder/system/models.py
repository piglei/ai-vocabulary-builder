from dataclasses import dataclass


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
class SystemSettings:
    """The system settings for the project."""

    model_provider: str
    openai_config: OpenAIConfig
    gemini_config: GeminiConfig


def build_default_settings() -> SystemSettings:
    """Build the default system settings, all fields are using the default value."""
    return SystemSettings(
        model_provider="",
        openai_config=OpenAIConfig(api_key="", api_host="", model=""),
        gemini_config=GeminiConfig(api_key="", api_host="", model=""),
    )
