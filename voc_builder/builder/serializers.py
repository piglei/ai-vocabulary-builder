"""Serializers for request inputs."""

from typing import List, Optional

import cattrs
from pydantic import BaseModel, Field

from voc_builder.builder.models import WordSample


class TranslatedTextInput(BaseModel):
    """A text with its translation.

    :param orig_text: The original text
    :param translated_text: The translated text
    """

    orig_text: str
    translated_text: str


class GetKnownWordsByTextInput(BaseModel):
    """The input data for getting known words by text."""

    text: str = Field(..., min_length=1)


class ManuallySelectInput(BaseModel):
    """The input data for a manually save."""

    orig_text: str = Field(..., min_length=1)
    translated_text: str = Field(..., min_length=1)
    word: str = Field(..., min_length=1)


class DeleteWordsInput(BaseModel):
    """The input data for deleting words.

    :param words: The list of words to be deleted.
    :param mark_mastered: If True, mark the words as mastered.
    """

    words: list[str]
    mark_mastered: bool = False


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
