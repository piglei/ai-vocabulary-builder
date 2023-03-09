"""functions related with the vocabulary builder(CSV)"""
import csv
import datetime
import logging
from pathlib import Path
from typing import Iterable, TextIO, Tuple

from rich.console import Console

from voc_builder import config
from voc_builder.models import WordSample
from voc_builder.store import get_word_store

logger = logging.getLogger()


class VocBuilderCSVFile:
    """A CSV file which stores the words

    :param file_path: The path of the .csv file
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def read_all_with_meta(self) -> Iterable[Tuple[WordSample, str]]:
        """Read all words from file, include extra metadata

        :return: List of (WordSample, date_added)
        """
        with open(self.file_path, 'r', encoding='utf-8') as fp:
            for row in self._get_reader(fp):
                t, tran_t = row['例句/翻译'].split(' / ', 1)
                w = WordSample(
                    word=row['单词'],
                    word_normal=None,
                    word_meaning=row['释义'],
                    pronunciation=row['读音'],
                    orig_text=t,
                    translated_text=tran_t,
                )
                yield w, row['添加时间']

    def _get_reader(self, fp: TextIO):
        """Get the CSV reader obj"""
        return csv.DictReader(fp, delimiter=",", quoting=csv.QUOTE_MINIMAL)


def get_csv_builder() -> VocBuilderCSVFile:
    """Get the builder for CSV file"""
    return VocBuilderCSVFile(config.DEFAULT_CSV_FILE_PATH)


def migrate_builder_data_to_store(console: Console):
    """Try to migrate the data in current builder csv file into new word store"""
    if not config.DEFAULT_CSV_FILE_PATH.exists():
        return

    console.print('> Legacy vocabulary CSV file found, starting a migration...')
    word_store = get_word_store()
    cnt = 0
    for w, date_added in get_csv_builder().read_all_with_meta():
        dt = datetime.datetime.strptime(date_added, '%Y-%m-%d %H:%M')
        word_store.add(w, ts_date_added=dt.timestamp())
        cnt += 1
        continue
    console.print(f'> {cnt} words have been migrated to the new word store.')

    # Turn the original CSV file into backup file so this migration process won't
    # start again.
    backup_file_path = str(config.DEFAULT_CSV_FILE_PATH) + '.bak'
    config.DEFAULT_CSV_FILE_PATH.rename(backup_file_path)
    console.print(f'The vocabulary CSV file was moved to {backup_file_path}.')
    console.print(
        'Please get the CSV file via [bold]aivoc export --format csv[/bold] command in the future.'
    )
