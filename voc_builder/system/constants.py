from enum import Enum
from typing import Optional

from attrs import define


class ModelProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"


@define
class Language:
    """A language."""

    code: str
    name: str


class TargetLanguage(Enum):
    """Supported target languages."""

    SIMPLIFIED_CHINESE = Language("zh-Hans", "Simplified Chinese")
    TRADITIONAL_CHINESE = Language("zh-Hant", "Traditional Chinese")
    ARABIC = Language("ar", "Arabic")
    FRENCH = Language("fr", "French")
    GERMAN = Language("de", "German")
    HINDI = Language("hi", "Hindi")
    JAPANESE = Language("ja", "Japanese")
    KOREAN = Language("ko", "Korean")
    RUSSIAN = Language("ru", "Russian")
    SPANISH = Language("es", "Spanish")
    PORTUGUESE = Language("pt", "Portuguese")

    @classmethod
    def get_by_code(cls, code: str) -> "Optional[TargetLanguage]":
        """Get a target language by its code."""
        for language in cls:
            if language.value.code == code:
                return language
        return None


# Available Gemini models
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-pro",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]

# Available OpenAI models
OPENAI_MODELS = [
    "chatgpt-4o-latest",
    "codex-mini-latest",
    "computer-use-preview",
    "computer-use-preview-2025-03-11",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-0301",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-16k-0613",
    "gpt-4",
    "gpt-4-0125-preview",
    "gpt-4-0314",
    "gpt-4-0613",
    "gpt-4-1106-preview",
    "gpt-4-32k",
    "gpt-4-32k-0314",
    "gpt-4-32k-0613",
    "gpt-4-turbo",
    "gpt-4-turbo-2024-04-09",
    "gpt-4-turbo-preview",
    "gpt-4-vision-preview",
    "gpt-4.1",
    "gpt-4.1-2025-04-14",
    "gpt-4.1-mini",
    "gpt-4.1-mini-2025-04-14",
    "gpt-4.1-nano",
    "gpt-4.1-nano-2025-04-14",
    "gpt-4o",
    "gpt-4o-2024-05-13",
    "gpt-4o-2024-08-06",
    "gpt-4o-2024-11-20",
    "gpt-4o-audio-preview",
    "gpt-4o-audio-preview-2024-10-01",
    "gpt-4o-audio-preview-2024-12-17",
    "gpt-4o-audio-preview-2025-06-03",
    "gpt-4o-mini",
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-mini-audio-preview",
    "gpt-4o-mini-audio-preview-2024-12-17",
    "gpt-4o-mini-search-preview",
    "gpt-4o-mini-search-preview-2025-03-11",
    "gpt-4o-search-preview",
    "gpt-4o-search-preview-2025-03-11",
    "gpt-5",
    "gpt-5-2025-08-07",
    "gpt-5-chat-latest",
    "gpt-5-codex",
    "gpt-5-mini",
    "gpt-5-mini-2025-08-07",
    "gpt-5-nano",
    "gpt-5-nano-2025-08-07",
    "gpt-5-pro",
    "gpt-5-pro-2025-10-06",
    "gpt-5.1",
    "gpt-5.1-2025-11-13",
    "gpt-5.1-chat-latest",
    "gpt-5.1-codex",
    "gpt-5.1-mini",
    "o1",
    "o1-2024-12-17",
    "o1-mini",
    "o1-mini-2024-09-12",
    "o1-preview",
    "o1-preview-2024-09-12",
    "o1-pro",
    "o1-pro-2025-03-19",
    "o3",
    "o3-2025-04-16",
    "o3-deep-research",
    "o3-deep-research-2025-06-26",
    "o3-mini",
    "o3-mini-2025-01-31",
    "o3-pro",
    "o3-pro-2025-06-10",
    "o4-mini",
    "o4-mini-2025-04-16",
    "o4-mini-deep-research",
    "o4-mini-deep-research-2025-06-26",
]

# Available Anthropic models
ANTHROPIC_MODELS = [
    "claude-3-5-haiku-20241022",
    "claude-3-5-haiku-latest",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-7-sonnet-20250219",
    "claude-3-7-sonnet-latest",
    "claude-3-haiku-20240307",
    "claude-3-opus-20240229",
    "claude-3-opus-latest",
    "claude-4-opus-20250514",
    "claude-4-sonnet-20250514",
    "claude-haiku-4-5",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-0",
    "claude-opus-4-1-20250805",
    "claude-opus-4-20250514",
    "claude-sonnet-4-0",
    "claude-sonnet-4-20250514",
    "claude-sonnet-4-5",
    "claude-sonnet-4-5-20250929",
]

DEEPSEEK_MODELS = [
    "deepseek-chat",
    "deepseek-reasoner",
]
