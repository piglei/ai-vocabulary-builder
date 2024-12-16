"""Serializers for request inputs."""

from typing import Any, Dict, Literal, Union

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from voc_builder.constants import ModelProvider


class DeleteWordsInput(BaseModel):
    """The input data for deleting words.

    :param words: The list of words to be deleted.
    :param mark_mastered: If True, mark the words as mastered.
    """

    words: list[str]
    mark_mastered: bool = False


class GetKnownWordsByTextInput(BaseModel):
    """The input data for getting known words by text."""

    text: str = Field(..., min_length=1)


class ManuallySelectInput(BaseModel):
    """The input data for a manually save."""

    orig_text: str = Field(..., min_length=1)
    translated_text: str = Field(..., min_length=1)
    word: str = Field(..., min_length=1)


class SettingsInput(BaseModel):
    """The input data for saving system settings"""

    model_provider: str
    openai_config: Dict[str, Any]
    gemini_config: Dict[str, Any]

    @field_validator("model_provider")
    @classmethod
    def validate_model_provider(cls, value):
        try:
            ModelProvider(value)
        except ValueError:
            raise ValueError("invalid model provider")
        return value


class OpenAIConfigInput(BaseModel):
    api_key: str = Field(..., min_length=1)
    api_host: Union[AnyHttpUrl, Literal[""]]
    model: str


class GeminiConfigInput(BaseModel):
    api_key: str = Field(..., min_length=1)
    api_host: Union[AnyHttpUrl, Literal[""]]
    model: str
    model: str


class DeleteMasteredWordsInput(BaseModel):
    """The input data for delete mastered words."""

    words: list[str]
