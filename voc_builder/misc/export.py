"""Handle exporting related functions"""

import csv
from typing import TextIO

from voc_builder.infras.store import get_word_store


class VocCSVWriter:
    """Write vocabulary book into CSV file

    :param fp: The file object
    """

    header_row = (
        "#",
        "Word",
        "Pronunciation",
        "Definition",
        "Example sentence / Translation",
        "Date added",
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
                    w.ws.get_definitions_str(),
                    "{} / {}".format(w.ws.orig_text, w.ws.translated_text),
                    w.date_added,
                )
            )

    def _get_writer(self, fp: TextIO):
        """Get the CSV writer obj"""
        return csv.writer(fp, delimiter=",", quoting=csv.QUOTE_MINIMAL)
