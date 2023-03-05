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
        items = set()
        MWord = Query()
        for word in words:
            if self._db.search(MWord.word == word):
                items.add(word)
        return items

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
