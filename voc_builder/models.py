from dataclasses import dataclass
from typing import Optional


@dataclass
class WordSample:
    """A word sample which is ready to be added into a vocabulary book

    :param word: The word itself, for example: "world"
    :param word_normal: The normal form of the given word, `None` means unknown
    :param word_meaning: The Chinese meaning of the word
    :param pronunciation: The pronunciation of the word, "/wɔrld/"
    :param orig_text: The original text
    :param translated_text: The translated text
    """

    word: str
    word_normal: Optional[str]
    word_meaning: str
    pronunciation: str
    orig_text: str
    translated_text: str

    @classmethod
    def make_empty(cls, word: str) -> 'WordSample':
        """Make an empty object which use "word" field only, other fields are set to empty."""
        return cls(word, word, '', '', '', '')

    def get_word_meaning_display(self) -> str:
        """Get the word_meaning field for display purpose, will add extra info"""
        if self.word_normal and self.word_normal != self.word:
            return f"{self.word_meaning}（原词：{self.word_normal}）"
        return self.word_meaning

    def get_normal_word_display(self) -> str:
        """Try to display current word with the normal form comes first"""
        if self.word_normal and self.word_normal != self.word:
            return f'{self.word_normal}({self.word})'
        return self.word


@dataclass
class WordChoice:
    """A word for choice

    :param word: The word itself, for example: "world"
    :param word_normal: The normal form of the given word
    :param word_meaning: The Chinese meaning of the word
    :param pronunciation: The pronunciation of the word, "/wɔrld/"
    """

    word: str
    word_normal: str
    word_meaning: str
    pronunciation: str

    def get_console_display(self) -> str:
        """A more detailed format"""
        if self.word == self.word_normal:
            return f'{self.word} / {self.pronunciation.strip("/")} / {self.word_meaning}'
        else:
            return f'{self.word} / （原词：{self.word_normal}） / {self.pronunciation.strip("/")} / {self.word_meaning}'

    @classmethod
    def extract_word(cls, s: str) -> str:
        """Extract the word from the console display

        :param s: A detailed representation of WordChoice object
        :return: The word string
        """
        return s.split(' / ')[0]


@dataclass
class WordProgress:
    """Store the learning progress of a word

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
class TranslationResult:
    """The result of a successful translation

    :param text: The original text.
    :param translated_text: The translated text.
    """

    text: str
    translated_text: str


@dataclass
class LiveTranslationInfo:
    """A live info represents an ongoing translation

    :param translated_text: Text being translated
    :param is_finished: Whether the translation is finished
    """

    translated_text: str = ''
    is_finished: bool = False


@dataclass
class LiveStoryInfo:
    """A live info represents an ongoing story writing

    :param story_text: Current story content
    :param is_finished: Whether the story writing is finished
    """

    story_text: str = ''
    is_finished: bool = False
