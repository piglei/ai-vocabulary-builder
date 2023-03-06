"""functions related with the vocabulary builder(CSV)"""
import csv
import datetime
import logging
import os
from pathlib import Path
from typing import Iterable, List, Optional, Set, TextIO, Tuple

from voc_builder import config
from voc_builder.models import WordSample

logger = logging.getLogger()


class VocBuilderCSVFile:
    """A CSV file which stores the words

    :param file_path: The path of the .csv file
    """

    header_row = ('添加时间', '单词', '读音', '释义', '例句/翻译')

    def __init__(self, file_path: Path):
        # Initialize the file if not exists
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as fp:
                self._get_writer(fp).writerow(self.header_row)

        self.file_path = file_path

    def append_word(self, w: WordSample, date_added: Optional[str] = None):
        """Append a word to the current file

        :param w: WordSample object
        :param date_added: When the word was added, use now() if not given
        """
        with open(self.file_path, 'a', encoding='utf-8') as fp:
            self._get_writer(fp).writerow(
                (
                    date_added if date_added else self.get_current_date(),
                    w.word,
                    w.pronunciation,
                    w.word_meaning,
                    '{} / {}'.format(w.orig_text, w.translated_text),
                )
            )

    def words_count(self) -> int:
        """Get the count of all words"""
        return len(self.read_all())

    def is_duplicated(self, word: WordSample) -> bool:
        """Check if a world is already presented in current file"""
        for w in self.read_all():
            if w.word == word.word:
                return True
        return False

    def read_all(self) -> List[WordSample]:
        """Read all words from file

        :return: List of WordSample objects
        """
        items = []
        for w, _ in self.read_all_with_meta():
            items.append(w)
        return items

    def read_all_with_meta(self) -> Iterable[Tuple[WordSample, str]]:
        """Read all words from file, include extra metadata

        :return: List of (WordSample, date_added)
        """
        with open(self.file_path, 'r', encoding='utf-8') as fp:
            for row in self._get_reader(fp):
                t, tran_t = row['例句/翻译'].split(' / ', 1)
                w = WordSample(
                    word=row['单词'],
                    word_meaning=row['释义'],
                    pronunciation=row['读音'],
                    orig_text=t,
                    translated_text=tran_t,
                )
                yield w, row['添加时间']

    def find_known_words(self, words: Set[str]) -> Set[str]:
        """Find out words already in record

        :param words: The source words which are tokenized from user text.
        """
        all_words = {w.word for w in self.read_all()}
        return words & all_words

    def remove_words(self, words: Set[str]):
        """Remove words from current records

        :param words: Words need to be removed.
        """
        # INFO: CSV does not support in-place update, so a fully update is required
        new_path = Path(str(self.file_path) + '.new')
        if new_path.exists():
            new_path.unlink()

        new_file = VocBuilderCSVFile(new_path)
        for w, date_added in self.read_all_with_meta():
            # Skip words
            if w.word in words:
                continue
            new_file.append_word(w, date_added)

        # Replace current file with new file
        os.rename(new_path, self.file_path)

    @staticmethod
    def get_current_date() -> str:
        """Return current date and time"""
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    def _get_reader(self, fp: TextIO):
        """Get the CSV reader obj"""
        return csv.DictReader(fp, delimiter=",", quoting=csv.QUOTE_MINIMAL)

    def _get_writer(self, fp: TextIO):
        """Get the CSV writer obj"""
        return csv.writer(fp, delimiter=",", quoting=csv.QUOTE_MINIMAL)


def get_csv_builder() -> VocBuilderCSVFile:
    """Get the builder for CSV file"""
    return VocBuilderCSVFile(config.DEFAULT_CSV_FILE_PATH)
