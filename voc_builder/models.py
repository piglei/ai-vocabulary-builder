import re
from dataclasses import dataclass
from typing import List, Optional

RE_PART_OF_SPEECH = re.compile(r"^\[([a-zA-Z]+)\]")


@dataclass
class WordDefinition:
    """A word definition"""

    part_of_speech: str
    definition: str

    @classmethod
    def from_text(cls, text: str) -> "WordDefinition":
        """Create a WordDefinition object from text like "[noun] ..."."""
        if m := RE_PART_OF_SPEECH.search(text):
            part_of_speech = m.group(1)
            definition = text[m.end() :].strip()
            return cls(part_of_speech, definition)
        return cls("", text)


@dataclass
class WordSample:
    """A word sample which is ready to be added into the vocabulary book.

    :param word: The word itself, for example: "world"
    :param word_normal: The normal form of the given word, `None` means unknown
    :param pronunciation: The pronunciation of the word, "/wɔrld/"
    :param definitions: The word's definitions
    :param orig_text: The original text
    :param translated_text: The translated text
    """

    word: str
    word_normal: Optional[str]
    pronunciation: str
    definitions: List[str]
    orig_text: str
    translated_text: str

    @classmethod
    def make_empty(cls, word: str) -> "WordSample":
        """Make an empty object which use "word" field only, other fields are set to empty."""
        return cls(word, word, "", [], "", "")

    def get_definitions_str(self) -> str:
        """Get the definitions as a single string."""
        defs = "; ".join(d.definition for d in self.get_structured_definitions())
        if self.word_normal and self.word_normal != self.word:
            return f"{defs}（原词：{self.word_normal}）"
        return defs

    def get_structured_definitions(self) -> List[WordDefinition]:
        """Get the structured definitions."""
        return [WordDefinition.from_text(d) for d in self.definitions]


@dataclass
class WordChoice:
    """A word for choice.

    :param word: The word itself, for example: "world"
    :param word_normal: The normal form of the given word
    :param pronunciation: The pronunciation of the word, "/wɔrld/"
    :param definitions: The definitions of the word
    """

    word: str
    word_normal: str
    pronunciation: str
    definitions: List[str]


@dataclass
class WordProgress:
    """Store the learning progress of a word.

    :param word: The word itself, for example: "world"
    :param quiz_cnt: The count of being used for quiz
    :param ts_date_quiz: The last time it was used for quiz, in UNIX timestamp
    :param storied_cnt: The count of being used for making story
    :param ts_date_storied: The last time it was used for making story, in UNIX timestamp
    """

    word: str
    quiz_cnt: int = 0
    ts_date_quiz: Optional[float] = None
    storied_cnt: int = 0
    ts_date_storied: Optional[float] = None


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
