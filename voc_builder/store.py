import copy
import datetime
import math
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import pendulum
from tinydb import Query, TinyDB

from voc_builder import config
from voc_builder.models import WordProgress, WordSample


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


@dataclass
class WordDetailedObj:
    """A detailed word object, including the WordSample, WordProgress and other data."""

    ws: WordSample
    wp: WordProgress
    ts_date_added: float

    @property
    def word(self) -> str:
        """A shortcut for retrieving word string"""
        return self.ws.word

    @property
    def date_added(self) -> str:
        """Return a well formatted date added string for display"""
        return datetime.datetime.fromtimestamp(self.ts_date_added).strftime('%Y-%m-%d %H:%M')

    @property
    def date_added_diff_for_humans(self) -> str:
        """Return a string like "3 days ago" or "2 hours ago" for display"""
        return pendulum.from_timestamp(self.ts_date_added).diff_for_humans()


class WordStore:
    """Stores all the words in vocabulary book

    :param file_path: the file path which stores data
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._db = TinyDB(self.file_path)

    def pick_story_words(self, count: int = 6) -> List[WordSample]:
        """Pick some words for writing story

        :param count: How many words to pick
        :return: A list of words
        """
        all_words = sorted(
            self.all(), key=lambda obj: (obj.wp.ts_date_storied or 0, obj.ts_date_added or 0)
        )
        # Randomize the result by picking from a slightly lager range
        results = all_words[: math.ceil(1.5 * count)]
        random.shuffle(results)
        return [obj.ws for obj in results][:count]

    def update_story_words(self, words: List[WordSample]):
        """Update the words being used for making story, so later picking won't get the
        identical results over and over again.
        """
        Word = Query()
        for w in words:
            obj = self.get(w.word)
            if not obj:
                continue

            # Increase the count being storied and update date
            wp = copy.copy(obj.wp)
            wp.storied_cnt += 1
            wp.ts_date_storied = time.time()
            self._db.update(
                {'wp': asdict(wp)},
                Word.ws.word == obj.ws.word,
            )

    def list_latest(self, limit: Optional[int] = None) -> List[WordDetailedObj]:
        """List latest added words

        :param limit: How many words to list, if not given, list all.
        :return: A list of detailed word objects.
        """
        results = sorted(self.all(), key=lambda obj: obj.ts_date_added)
        if limit is not None:
            return results[-limit:]
        else:
            return results

    def filter(self, words: Set[str]) -> Set[str]:
        """Filter the given word list, return those exists in current db

        :param words: a list of lower cased word.
        """
        return {word for word in words if self.exists(word)}

    def add(self, word: WordSample, ts_date_added: Optional[float] = None):
        """Add a word to the vocabulary book

        :param ts_date_added: If given, use this value as date added instead.
        """
        Word = Query()
        return self._db.upsert(
            {
                'ws': asdict(word),
                'wp': asdict(WordProgress(word=word.word)),
                'ts_date_added': ts_date_added if ts_date_added is not None else time.time(),
            },
            Word.ws.word == word.word,
        )

    def count(self) -> int:
        """The count of all words in store"""
        return len(self._db.all())

    def get(self, word: str) -> Optional[WordDetailedObj]:
        """Get a result by word string

        :return: None if no word can be found
        """
        Word = Query()
        objs = self._db.search(Word.ws.word == word)
        if not objs:
            return None

        return self._to_detailed_obj(objs[0])

    def all(self) -> Iterable[WordDetailedObj]:
        """Return all words and progresses objects

        :return: Detailed word objects.
        """
        for d in self._db.all():
            yield self._to_detailed_obj(d)

    def search(self, keyword: str, order_by: str = 'date_added') -> Iterable[WordDetailedObj]:
        """Search for words by keyword

        :param keyword: The search keyword, part of a word.
        :param order_by: The order of the result.
        :return: A generator of detailed word objects.
        """
        results = sorted(self.all(), key=lambda obj: obj.ts_date_added)
        for obj in results:
            if keyword.lower() in obj.ws.word.lower():
                yield obj

    def remove(self, word: str) -> List[int]:
        """Remove a word

        :param word: Lower cased word.
        :return: A list of removed doc ID
        """
        Word = Query()
        return self._db.remove(Word.ws.word == word)

    def exists(self, word: str):
        """Check if a word exists in current db

        :param word: Lower cased word.
        """
        Word = Query()
        return bool(self._db.search(Word.ws.word == word))

    @staticmethod
    def _to_detailed_obj(d: Dict) -> WordDetailedObj:
        """Turn raw JSON data into WordDetailedObj object."""
        # Handle data <= 0.2.0 version
        d['ws'].setdefault('word_normal', None)
        return WordDetailedObj(
            ws=WordSample(**d['ws']),
            wp=WordProgress(**d['wp']),
            ts_date_added=d['ts_date_added'],
        )


@dataclass
class InternalState:
    """The internal state of current tool

    :param name: Use a fixed value by default.
    :param last_ver_checking_ts: The last time when a version checking is performed, in Unix timestamp.
    """

    name: str
    last_ver_checking_ts: float


class InternalStateStore:
    """Stores the internal state of the tool itself.

    :param file_path: The file path which stores data.
    """

    name_default = 'default'

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._db = TinyDB(self.file_path)

    def set_last_ver_checking_ts(self):
        """Update the last version checking time, set to current."""
        State = Query()
        return self._db.upsert(
            {
                'name': self.name_default,
                'last_ver_checking_ts': time.time(),
            },
            State.name == self.name_default,
        )

    def get_last_ver_checking_ts(self) -> Optional[float]:
        """Get the last version checking time"""
        State = Query()
        objs = self._db.search(State.name == self.name_default)
        if not objs:
            return None
        return InternalState(**objs[0]).last_ver_checking_ts


# Database related functions

_db_initialized = False


def initialized_db():
    """Set up databases, make global objects"""
    global _db_initialized
    _db_initialized = True
    config.DEFAULT_DB_PATH.mkdir(exist_ok=True)


def get_mastered_word_store() -> MasteredWordStore:
    if not _db_initialized:
        initialized_db()
    return MasteredWordStore(config.DEFAULT_DB_PATH / 'mastered_word.json')


def get_word_store() -> WordStore:
    if not _db_initialized:
        initialized_db()
    return WordStore(config.DEFAULT_DB_PATH / 'word.json')


def get_internal_state_store() -> InternalStateStore:
    if not _db_initialized:
        initialized_db()
    return InternalStateStore(config.DEFAULT_DB_PATH / 'internal.json')
