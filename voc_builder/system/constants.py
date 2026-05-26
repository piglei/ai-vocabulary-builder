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
