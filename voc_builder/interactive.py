"""Functions relative with the interactive REPL"""
import logging
import traceback
from dataclasses import dataclass
from textwrap import dedent
from typing import ClassVar, Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from voc_builder import config
from voc_builder.builder import get_csv_builder
from voc_builder.exceptions import VocBuilderError, WordInvalidForAdding
from voc_builder.models import WordChoice, WordSample
from voc_builder.openai_svc import get_word_and_translation, get_word_choices
from voc_builder.store import get_mastered_word_store
from voc_builder.utils import tokenize_text

logger = logging.getLogger()
console = Console()

# Special commands
# no: discard last added word, try to get other options and let user choose from them manually
COMMAND_NO = 'no'


class LastActionResult:
    """This class is used as a global state, stores the result of last action"""

    trans_result: ClassVar[Optional['TransActionResult']] = None


@dataclass
class TransActionResult:
    """The result of a translation action

    :param input_text: The text user has inputted
    :param stored_to_voc_book: whether the word has been added to the vocabulary book
    :param error: The actual error message
    :param word_sample: The WordSample object
    """

    input_text: str
    stored_to_voc_book: bool
    error: str = ''
    word_sample: Optional[WordSample] = None


def enter_interactive_mode():
    """Enter the interactive mode"""
    console.print(
        Panel(
            dedent(
                f'''
    [bold]Guides[/bold]:
    - Enter your text to start translating and building vocabulary
    - One sentence at a time, don't paste huge amounts of text at once
    - The vocabulary book file can be found at [bold]{config.DEFAULT_CSV_FILE_PATH}[/bold]
    - Special Command:
        * [bold]no[/bold]: remove the last added word and start a manual selection
        * [Ctrl+c] to quit'''
            ).strip(),
            title='Welcome to AI Vocabulary Builder!',
        )
    )
    while True:
        text = Prompt.ask('[blue]>[/blue] Enter text').strip()
        if not text:
            continue
        elif text == COMMAND_NO:
            handle_cmd_no()
            continue

        LastActionResult.trans_result = handle_cmd_trans(text.strip())


def handle_cmd_no():
    """Handle the "no" command, do following things:

    - Remove the last added word, also mark it as "mastered"
    - Let the user choose unknown word manually
    """
    ret = LastActionResult.trans_result
    if not (ret and ret.stored_to_voc_book):
        console.print('The "no" command was used to remove the last added word and select the word manually.')
        console.print('Can\'t get the last added word, please start a new translation first.')
        return

    assert ret.word_sample
    # Remove last word, mark as mastered
    console.print(f'"{ret.word_sample.word}" was discarded, preparing other words...', style='grey42')
    get_csv_builder().remove_words({ret.word_sample.word})
    get_mastered_word_store().add(ret.word_sample.word)

    make_choice_manually(ret.input_text, ret.word_sample.translated_text)
    # Reset last action
    LastActionResult.trans_result = None


def make_choice_manually(text: str, translated_text: str):
    """Extract 3 most uncommon words, let the user select from them manually

    :param translated_text: The full content of translated text.
    """
    builder = get_csv_builder()
    mastered_word_s = get_mastered_word_store()

    progress = Progress(SpinnerColumn(), TextColumn("[bold blue] Querying OpenAI API"))
    orig_words = tokenize_text(text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = builder.find_known_words(orig_words) | mastered_word_s.filter(orig_words)
    with progress:
        task_id = progress.add_task("get", start=False)
        try:
            choices = get_word_choices(text, known_words)
        except VocBuilderError as e:
            console.print(f'[red] Error processing text, detail: {e}[red]')
            logger.debug('Detailed stack trace info: %s', traceback.format_exc())
            return
        finally:
            progress.update(task_id, total=1, advance=1)

    if not choices:
        console.print('No words could be extracted from the text you given, skip.', style='grey42')
        return

    # Read user input
    choice_skip = 'None of above, skip for now.'
    str_choices = [w.get_console_display() for w in choices] + [choice_skip]
    answer = questionary.select("Choose the word you don't know", choices=str_choices).ask()
    if answer == choice_skip:
        console.print('Skipped.', style='grey42')
        return

    # Get the WordChoice, turn it into WordSample and save to vocabulary book
    word_choice = next(w for w in choices if w.word == WordChoice.extract_word(answer))
    word = WordSample(
        word=word_choice.word,
        word_meaning=word_choice.word_meaning,
        pronunciation=word_choice.pronunciation,
        translated_text=translated_text,
        orig_text=text,
    )

    try:
        validate_result_word(word, text)
    except WordInvalidForAdding as e:
        console.print(f'Unable to add "{word.word}", reason: {e}', style='grey42')
        return

    builder.append_word(word)
    console.print(
        (
            f'[bold]"{word.word}"[/bold] was added to your vocabulary book ([bold]{builder.words_count()}[/bold] '
            'in total), well done!'
        ),
        style='grey42',
    )
    return


def handle_cmd_trans(text: str):
    """Write a new word to the vocabulary book

    :param csv_book_path: The path of vocabulary book
    """
    builder = get_csv_builder()
    mastered_word_s = get_mastered_word_store()

    progress = Progress(SpinnerColumn(), TextColumn("[bold blue] Querying OpenAI API"))
    orig_words = tokenize_text(text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = builder.find_known_words(orig_words) | mastered_word_s.filter(orig_words)
    with progress:
        task_id = progress.add_task("get", start=False)
        try:
            word = get_word_and_translation(text, known_words)
        except VocBuilderError as e:
            console.print(f'[red] Error processing text, detail: {e}[red]')
            logger.debug('Detailed stack trace info: %s', traceback.format_exc())
            return TransActionResult(input_text=text, stored_to_voc_book=False, error=str(e))
        finally:
            progress.update(task_id, total=1, advance=1)

    console.print(format_as_console_table(word))

    try:
        validate_result_word(word, text)
    except WordInvalidForAdding as e:
        console.print(f'Unable to add "{word.word}", reason: {e}', style='grey42')
        return TransActionResult(input_text=text, stored_to_voc_book=False, error=str(e))

    builder.append_word(word)
    console.print(
        (
            f'[bold]"{word.word}"[/bold] was added to your vocabulary book ([bold]{builder.words_count()}[/bold] '
            'in total), well done!'
        ),
        style='grey42',
    )
    return TransActionResult(input_text=text, stored_to_voc_book=True, word_sample=word)


def validate_result_word(word: WordSample, orig_text: str):
    """Check if a result word is valid before it can be put into vocabulary book"""
    if get_csv_builder().is_duplicated(word):
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
