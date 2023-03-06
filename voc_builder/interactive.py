from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Optional

import questionary
from rich.progress import Progress, SpinnerColumn, TextColumn

from voc_builder.exceptions import VocBuilderError, WordInvalidForAdding
from voc_builder.main import (
    DEFAULT_CSV_FILE_PATH,
    VocBuilderCSVFile,
    console,
    get_mastered_word_store,
    validate_result_word,
)
from voc_builder.models import WordChoice, WordSample
from voc_builder.openai_svc import get_word_choices
from voc_builder.utils import tokenize_text

# Special commands
# discard last added word, try to get other options and let user choose manually
COMMAND_NO = 'no'


class LastActionResult:
    """This class is used as a global state, stores the result of last action"""

    result: ClassVar[Optional['ActionResult']] = None


@dataclass
class ActionResult:
    """The result of a translation action

    :param input_text: The text user has inputted
    :param stored_to_voc_book: whether the word has been added to vocabulary book
    :param error: The actual error message
    :param word_sample: The WordSample object
    """

    input_text: str
    stored_to_voc_book: bool
    error: str = ''
    word_sample: Optional[WordSample] = None


def handle_command_no(csv_book_path: Path = DEFAULT_CSV_FILE_PATH):
    """Handle the "no" command, do following things:

    - Remove the last added word, also mark it as "mastered"
    - Let the user choose unknown word manually
    """
    ret = LastActionResult.result
    if not (ret and ret.stored_to_voc_book):
        console.print('The command was used to remove last added word and choose word manually.')
        console.print('Can\'t find any added word, please start a new translation.')
        return

    assert ret.word_sample
    # Remove last word, mark as mastered
    console.print(f'Removed "{ret.word_sample.word}", preparing other words...', style='grey42')
    builder = VocBuilderCSVFile(csv_book_path)
    get_mastered_word_store().add(ret.word_sample.word)
    builder.remove_words({ret.word_sample.word})

    make_choice_manually(ret.input_text, ret.word_sample.translated_text, csv_book_path)
    # Reset last action
    LastActionResult.result = None


def make_choice_manually(
    text: str,
    translated_text: str,
    csv_book_path: Path = DEFAULT_CSV_FILE_PATH,
):
    """Extract 3 most uncommon words, let the user choice manually

    :param csv_book_path: The path of vocabulary book
    """
    builder = VocBuilderCSVFile(csv_book_path)
    mastered_word_s = get_mastered_word_store()

    progress = Progress(SpinnerColumn(), TextColumn("[bold blue] Querying OpenAI API"))
    orig_words = tokenize_text(text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = builder.find_known_words(orig_words) | mastered_word_s.filter(orig_words)
    with progress:
        task_id = progress.add_task("get", start=False)
        try:
            choices = get_word_choices(text, known_words)
            progress.update(task_id, total=1, advance=1)
        except VocBuilderError as e:
            console.print(f'[red] Error processing text, detail: {e}[red]')
            progress.update(task_id, total=1, advance=1)
            return

    if not choices:
        console.print('No words can be extracted from the text you given, skip.', style='grey42')
        return

    choice_skip = 'None of this above, skip for now.'
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
        validate_result_word(word, text, builder)
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
