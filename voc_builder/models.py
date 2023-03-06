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


@dataclass
class WordChoice:
    """A word for choice

    :param word: The word itself, for example: "world"
    :param word_meaning: The Chinese meaning of the word
    :param pronunciation: The pronunciation of the word, "/wɔrld/"
    """

    word: str
    word_meaning: str
    pronunciation: str

    def get_console_display(self) -> str:
        """A more detailed format"""
        return f'{self.word} / {self.pronunciation.strip("/")} / {self.word_meaning}'

    @classmethod
    def extract_word(cls, s: str) -> str:
        """Extract the word from the console display

        :param s: A detailed representation of WordChoice object
        :return: The word string
        """
        return s.split(' / ')[0]
