"""Serializers for request inputs."""

from typing import Any, Dict, List, Literal, Optional, Union

import cattrs
from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from voc_builder.constants import ModelProvider
from voc_builder.models import WordSample


class WordSampleOutput(BaseModel):
    """The output structure for word sample."""

    word: str
    word_normal: Optional[str]
    pronunciation: str
    orig_text: str
    definitions: List[str]
    translated_text: str

    # Extra fields from the WordSample object
    simple_definition: str
    structured_definitions: list[dict[str, str]]

    @classmethod
    def from_db_obj(cls, ws: WordSample) -> "WordSampleOutput":
        """Create an instance from a WordSample object."""
        d = cattrs.unstructure(ws)
        defs = ws.get_structured_definitions()
        return cls(
            simple_definition=ws.get_definitions_str(),
            structured_definitions=cattrs.unstructure(defs),
            **d,
        )


class TranslatedTextInput(BaseModel):
    """A text with its translation.

    :param orig_text: The original text
    :param translated_text: The translated text
    """

    orig_text: str
    translated_text: str


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


class DeleteMasteredWordsInput(BaseModel):
    """The input data for delete mastered words."""

    words: list[str]


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

    @field_validator("model")
    @classmethod
    def validate_model(cls, value):
        if not value:
            raise ValueError("model is required")
        return value


class GeminiConfigInput(BaseModel):
    api_key: str = Field(..., min_length=1)
    api_host: Union[AnyHttpUrl, Literal[""]]
    model: str

    @field_validator("model")
    @classmethod
    def validate_model(cls, value):
        if not value:
            raise ValueError("model is required")
        return value
