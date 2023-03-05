from pathlib import Path
from typing import List, Set

from tinydb import Query, TinyDB


class MasteredWordStore:
    """Stores words the user has already mastered

    :param file_path: the file path which stores data
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._db = TinyDB(self.file_path)

    def filter(self, words: Set[str]) -> Set[str]:
        """Filter the given word list, return those exists in current db

        :param words: a list of lower cased word.
        """
        return {word for word in words if self.exists(word)}

    def all(self) -> List[str]:
        """Return all mastered words

        :return: List of words.
        """
        return [d['word'] for d in self._db.all()]

    def add(self, word: str):
        """Mark a word as mastered

        :param word: Lower cased word.
        """
        MWord = Query()
        return self._db.upsert({'word': word}, MWord.word == word)

    def remove(self, word: str):
        """Remove a word

        :param word: Lower cased word.
        """
        MWord = Query()
        self._db.remove(MWord.word == word)

    def exists(self, word: str):
        """Check if a word exists in current db

        :param word: Lower cased word.
        """
        MWord = Query()
        return bool(self._db.search(MWord.word == word))
