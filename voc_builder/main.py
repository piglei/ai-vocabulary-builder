"""Main entrance of AI Vocabulary Builder"""
import csv
import datetime
import logging
import os
import sys
from pathlib import Path
from textwrap import dedent
from typing import List, Set, TextIO

import click
import openai
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from voc_builder.exceptions import VocBuilderError, WordInvalidForAdding
from voc_builder.models import WordSample
from voc_builder.openai_svc import parse_openai_reply, query_openai
from voc_builder.store import MasteredWordStore
from voc_builder.utils import tokenize_text

# Set logging to stdout by default
log_format = "%(asctime)s - %(name)s - [%(levelname)s]:  %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)

logger = logging.getLogger()

# The default path for storing the vocabulary book
DEFAULT_CSV_FILE_PATH = Path('~/aivoc_builder.csv').expanduser()
# The default path for storing db files, testings should patch this variable
DEFAULT_DB_PATH = Path('~/.aivoc_db').expanduser()

console = Console()


def write_new_one(text: str, csv_book_path: Path = DEFAULT_CSV_FILE_PATH):
    """Write a new word to the vocabulary book

    :param csv_book_path: The path of vocabulary book
    """
    from voc_builder.interactive import ActionResult

    builder = VocBuilderCSVFile(csv_book_path)
    mastered_word_s = get_mastered_word_store()

    progress = Progress(SpinnerColumn(), TextColumn("[bold blue] Querying OpenAI API"))
    orig_words = tokenize_text(text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = builder.find_known_words(orig_words) | mastered_word_s.filter(orig_words)
    with progress:
        task_id = progress.add_task("get", start=False)
        try:
            word = get_word_and_translation(text, known_words)
            progress.update(task_id, total=1, advance=1)
        except VocBuilderError as e:
            console.print(f'[red] Error processing text, detail: {e}[red]')
            progress.update(task_id, total=1, advance=1)
            return ActionResult(input_text=text, stored_to_voc_book=False, error=str(e))

    console.print(format_as_console_table(word))

    try:
        validate_result_word(word, text, builder)
    except WordInvalidForAdding as e:
        console.print(f'Unable to add "{word.word}", reason: {e}', style='grey42')
        return ActionResult(input_text=text, stored_to_voc_book=False, error=str(e))

    builder.append_word(word)
    console.print(
        (
            f'[bold]"{word.word}"[/bold] was added to your vocabulary book ([bold]{builder.words_count()}[/bold] '
            'in total), well done!'
        ),
        style='grey42',
    )
    return ActionResult(input_text=text, stored_to_voc_book=True, word_sample=word)


def validate_result_word(word: WordSample, orig_text: str, builder: 'VocBuilderCSVFile'):
    """Check if a result word is valid before it can be put into vocabulary book"""
    if builder.is_duplicated(word):
        raise WordInvalidForAdding('already in your vocabulary book')
    if get_mastered_word_store().exists(word.word):
        raise WordInvalidForAdding('already mastered')
    if word.word not in orig_text.lower():
        raise WordInvalidForAdding('not in the original text')


def format_as_console_table(word: WordSample) -> Table:
    """Format a word sample as rich table"""
    table = Table(title="翻译结果", show_header=False)
    table.add_column("title")
    table.add_column("detail", overflow='fold')
    table.add_row("[bold]原文[/bold]", f'[grey42]{word.orig_text}[grey42]')
    table.add_row("[bold]中文翻译[/bold]", word.translated_text)
    table.add_row("[bold]生词（自动提取）[/bold]", word.word)
    table.add_row("[bold]释义[/bold]", word.word_meaning)
    table.add_row("[bold]发音[/bold]", word.pronunciation)
    return table


class VocBuilderCSVFile:
    """A CSV file which stores the words

    :param file_path: The path of the .csv file
    """

    header_row = ('添加时间', '单词', '读音', '释义', '例句/翻译')

    def __init__(self, file_path: Path):
        # Initialize the file if not exists
        if not file_path.exists():
            with open(file_path, 'w') as fp:
                self._get_writer(fp).writerow(self.header_row)

        self.file_path = file_path

    def append_word(self, w: WordSample):
        """Append a word to the current file

        :param w: WordSample object
        """
        with open(self.file_path, 'a') as fp:
            self._get_writer(fp).writerow(
                (
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
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
        words = []
        with open(self.file_path, 'r') as fp:
            for row in self._get_reader(fp):
                t, tran_t = row['例句/翻译'].split(' / ', 1)
                w = WordSample(
                    word=row['单词'],
                    word_meaning=row['释义'],
                    pronunciation=row['读音'],
                    orig_text=t,
                    translated_text=tran_t,
                )
                words.append(w)
        return words

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
        for w in self.read_all():
            # Skip words
            if w.word in words:
                continue
            new_file.append_word(w)

        # Replace current file with new file
        os.rename(new_path, self.file_path)

    def _get_reader(self, fp: TextIO):
        """Get the CSV reader obj"""
        return csv.DictReader(fp, delimiter=",", quoting=csv.QUOTE_MINIMAL)

    def _get_writer(self, fp: TextIO):
        """Get the CSV writer obj"""
        return csv.writer(fp, delimiter=",", quoting=csv.QUOTE_MINIMAL)


def get_word_and_translation(text: str, known_words: Set[str]) -> WordSample:
    """Get the most uncommon word in the given text, the result also include other
    information such as meaning of the word and etc.

    :param text: The text which needs to be translated
    :param known_words: Words already known
    :return: a `WordSample` object
    :raise VocBuilderError: when unable to finish the API call or reply is malformed
    """
    try:
        reply = query_openai(text, known_words)
    except Exception as e:
        raise VocBuilderError('Error querying OpenAI API: %s' % e)
    try:
        return parse_openai_reply(reply, text)
    except ValueError as e:
        raise VocBuilderError(e)


# Database related functions

_db_initialized = False


def initialized_db():
    """Set up databases, make global objects"""
    global _db_initialized
    _db_initialized = True
    Path(DEFAULT_DB_PATH).mkdir(exist_ok=True)


def get_mastered_word_store() -> MasteredWordStore:
    if not _db_initialized:
        initialized_db()
    return MasteredWordStore(Path(DEFAULT_DB_PATH) / 'mastered_word.json')


@click.command()
@click.option('--api-key', envvar='OPENAI_API_KEY', required=True, help='Your OpenAI API key')
@click.option('--text', type=str, help='Text to be translated, interactive mode also supported')
@click.option(
    '--log-level', type=str, default='INFO', help='Log level, change it to DEBUG to see more logs'
)
def main(api_key: str, text: str, log_level: str):
    # Set logging level
    logger.setLevel(getattr(logging, log_level.upper()))

    openai.api_key = api_key

    # Read text either from command line or stdin
    if text:
        write_new_one(text.strip())
        return
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
        write_new_one(text.strip())
        return

    # No text found, enter interactive mode
    console.print(
        Panel(
            dedent(
                f'''
    [bold]Guides[/bold]:
    - Input one sentence at a time, don't paste huge amounts of text
    - The vocabulary book can be found in [bold]{DEFAULT_CSV_FILE_PATH}[/bold]
    - Press Ctrl+c to quit'''
            ).strip(),
            title='Welcome to AI Vocabulary Builder!',
        )
    )

    # TODO: Refactor to fix circular import
    from voc_builder.interactive import COMMAND_NO, handle_command_no
    from voc_builder.interactive import LastActionResult

    while True:
        text = Prompt.ask('[blue]>[/blue] Enter text').strip()
        if not text.strip():
            continue
        if text == COMMAND_NO:
            handle_command_no()
            continue

        LastActionResult.result = write_new_one(text.strip())


if __name__ == '__main__':
    main()
