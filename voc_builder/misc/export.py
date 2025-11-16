"""Handle exporting related functions"""

import csv
import random
import tempfile
from typing import BinaryIO, Iterable, TextIO

import genanki

from voc_builder.infras.store import WordDetailedObj, get_word_store


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


class AnkiDeckWriter:
    """Build an Anki deck with customized styling."""

    css = """
.card {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 16px;
}
.word {
  font-size: 32px;
  font-weight: 500;
  margin-bottom: 14px;
}
.example {
  line-height: 1.5;
  margin-bottom: 14px;
}
.translation {
  font-size: 16px;
  color: #333;
  margin-top: 14px;
  margin-bottom: 14px;
}
.pronunciation {
  font-size: 12px;
  color: #999;
  font-decoration: italic;
  margin-top: 14px;
  margin-bottom: 8px;
}
.definitions {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}
""".strip()

    def write(
        self,
        fp: BinaryIO,
        words: Iterable[WordDetailedObj],
        deck_name: str,
    ):
        """Write Anki deck data into the file-like object."""
        # Use a random deck and model ID to avoid conflicts
        deck_id = random.randrange(1 << 30, 1 << 31)
        model_id = random.randrange(1 << 30, 1 << 31)
        model = genanki.Model(
            model_id,
            "AI Vocabulary Builder Model",
            fields=[
                {"name": "Word"},
                {"name": "Example"},
                {"name": "Translation"},
                {"name": "Pronunciation"},
                {"name": "Definitions"},
            ],
            templates=[
                {
                    "name": "Vocabulary Card",
                    "qfmt": """
<div class="card">
  <div class="word">{{Word}}</div>
  <div class="example">{{Example}}</div>
</div>
""".strip(),
                    "afmt": """
{{FrontSide}}
<hr id="answer">
<div class="translation">{{Translation}}</div>
<div class="pronunciation">{{Pronunciation}}</div>
<div class="definitions">{{Definitions}}</div>
""".strip(),
                }
            ],
            css=self.css,
        )

        deck = genanki.Deck(deck_id, deck_name)
        sanitized_words = list(words)
        for word_obj in sanitized_words:
            note = genanki.Note(
                model=model,
                fields=[
                    word_obj.ws.word,
                    word_obj.ws.orig_text,
                    word_obj.ws.translated_text,
                    word_obj.ws.pronunciation,
                    word_obj.ws.get_definitions_str(),
                ],
            )
            deck.add_note(note)

        package = genanki.Package(deck)
        with tempfile.NamedTemporaryFile(suffix=".apkg") as tmp_file:
            package.write_to_file(tmp_file.name)
            tmp_file.seek(0)
            fp.write(tmp_file.read())
            fp.seek(0)
