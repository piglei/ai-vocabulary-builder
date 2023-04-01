"""Handle export command"""
import csv
import sys
from enum import Enum
from typing import Optional, TextIO

from rich.console import Console
from rich.table import Table

from voc_builder.store import get_word_store
from voc_builder.utils import highlight_words

console = Console()


class FormatType(Enum):
    ASCII = 'ascii'
    CSV = 'csv'


def handle_export(format: str, file_path: Optional[str]):
    """Handle the export command

    :param format: The output format, e.g. "ascii", "csv".
    :param file_path: The file path where the output will be written, if not specified,
        use stdout
    """
    if format == FormatType.ASCII.value:
        table = build_ascii_table()
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as fp:
                Console(file=fp).print(table)
                console.print(f'Exported to "{file_path}" successfully, format: ascii.')
        else:
            console.print(table)
        return
    elif format == FormatType.CSV.value:
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as fp:
                VocCSVWriter().write_to(fp)
                console.print(f'Exported to "{file_path}" successfully, format: csv.')
        else:
            VocCSVWriter().write_to(sys.stdout)
        return


def build_ascii_table() -> Table:
    """Build the Table object for display"""
    table = Table(title='', show_header=True)
    table.add_column("#")
    table.add_column("Word")
    table.add_column("Pronunciation")
    table.add_column("Definition", overflow='fold', max_width=24)
    table.add_column("Example sentence / Translation", overflow='fold')
    table.add_column("Date added")
    for i, w in enumerate(get_word_store().all(), start=1):
        table.add_row(
            str(i),
            w.word,
            w.ws.pronunciation,
            w.ws.get_word_meaning_display(),
            highlight_words(w.ws.orig_text, [w.word]) + '\n' + w.ws.translated_text,
            w.date_added,
        )
    return table


class VocCSVWriter:
    """Write vocabulary book into CSV file

    :param fp: The file object
    """

    header_row = (
        '#',
        'Word',
        'Pronunciation',
        'Definition',
        'Example sentence / Translation',
        'Date added',
    )

    def write_to(self, fp: TextIO):
        """Write to the given file object"""
        self._get_writer(fp).writerow(self.header_row)
        for i, w in enumerate(get_word_store().all(), start=1):
            self._get_writer(fp).writerow(
                (
                    str(i),
                    w.word,
                    w.ws.pronunciation,
                    w.ws.get_word_meaning_display(),
                    '{} / {}'.format(w.ws.orig_text, w.ws.translated_text),
                    w.date_added,
                )
            )

    def _get_writer(self, fp: TextIO):
        """Get the CSV writer obj"""
        return csv.writer(fp, delimiter=",", quoting=csv.QUOTE_MINIMAL)
