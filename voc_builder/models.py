from dataclasses import dataclass


@dataclass
class WordSample:
    """A word sample which is ready to be added into a vocabulary book

    :param word: The word itself, for example: "world"
    :param word_meaning: The Chinese meaning of the word
    :param pronunciation: The pronunciation of the word, "/wɔrld/"
    :param orig_text: The original text
    :param translated_text: The translated text
    """

    word: str
    word_meaning: str
    pronunciation: str
    orig_text: str
    translated_text: str

    @classmethod
    def make_empty(cls, word: str) -> 'WordSample':
        """Make an empty object which use "word" field only, other fields are set to empty."""
        return cls(word, '', '', '', '')
