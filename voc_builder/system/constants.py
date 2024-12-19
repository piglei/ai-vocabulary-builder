from enum import Enum
from typing import Optional

from attrs import define


class ModelProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"


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
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-2.0-flash-exp",
]

# Available OpenAI models
OPENAI_MODELS = [
    "o1-preview",
    "o1-preview-2024-09-12",
    "o1-mini",
    "o1-mini-2024-09-12",
    "gpt-4o",
    "gpt-4o-2024-11-20",
    "gpt-4o-2024-08-06",
    "gpt-4o-2024-05-13",
    "gpt-4o-realtime-preview",
    "gpt-4o-realtime-preview-2024-10-01",
    "gpt-4o-audio-preview",
    "gpt-4o-audio-preview-2024-10-01",
    "chatgpt-4o-latest",
    "gpt-4o-mini",
    "gpt-4o-mini-2024-07-18",
    "gpt-4-turbo",
    "gpt-4-turbo-2024-04-09",
    "gpt-4-0125-preview",
    "gpt-4-turbo-preview",
    "gpt-4-1106-preview",
    "gpt-4-vision-preview",
    "gpt-4",
    "gpt-4-0314",
    "gpt-4-0613",
    "gpt-4-32k",
    "gpt-4-32k-0314",
    "gpt-4-32k-0613",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-0301",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-16k-0613",
]

# Available Anthropic models
ANTHROPIC_MODELS = [
    "claude-3-5-haiku-latest",
    "claude-3-5-sonnet-latest",
    "claude-3-opus-latest",
]
