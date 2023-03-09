"""Functions relative with the interactive REPL"""
import logging
import traceback
from dataclasses import dataclass, field
from textwrap import dedent
from typing import ClassVar, List, Optional

import questionary
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from voc_builder.builder import migrate_builder_data_to_store
from voc_builder.exceptions import OpenAIServiceError, WordInvalidForAdding
from voc_builder.models import WordChoice, WordSample
from voc_builder.openai_svc import get_story, get_word_and_translation, get_word_choices
from voc_builder.store import get_mastered_word_store, get_word_store
from voc_builder.utils import highlight_words, tokenize_text, highlight_story_text

logger = logging.getLogger()
console = Console()

# Special commands
# no: discard last added word, try to get other options and let user choose from them manually
COMMAND_NO = 'no'
# story: make a stroy from least recent used words
COMMAND_STORY = 'story'


class LastActionResult:
    """This class is used as a global state, stores the result of last action"""

    trans_result: ClassVar[Optional['TransActionResult']] = None
    story_result: ClassVar[Optional['StoryActionResult']] = None


@dataclass
class TransActionResult:
    """The result of a translation action

    :param input_text: The text user has inputted
    :param stored_to_voc_book: whether the word has been added to the vocabulary book
    :param error: The actual error message
    :param invalid_for_adding: There is a valid word but it's invalid for adding
    :param word_sample: The WordSample object
    """

    input_text: str
    stored_to_voc_book: bool
    error: str = ''
    word_sample: Optional[WordSample] = None
    invalid_for_adding: bool = False


@dataclass
class NoActionResult:
    """The result of a "story" action

    :param word: The word user has selected
    :param stored_to_voc_book: whether the word has been saved
    :param error: The actual error message
    """

    word: Optional[WordSample] = None
    stored_to_voc_book: bool = False
    error: str = ''


@dataclass
class StoryActionResult:
    """The result of a story action

    :param words: The words for writing story
    :param error: The actual error message
    """

    words: List[WordSample] = field(default_factory=list)
    error: str = ''


prompt_style = Style.from_dict(
    {
        # Prompt
        "tip": "bold",
        "arrow": "bold",
    }
)


def enter_interactive_mode():
    """Enter the interactive mode"""
    # Try to migrate the data in the CSV file(for version < 0.2) to the new word store which was
    # based on TinyDB, this should be a one off action.
    try:
        migrate_builder_data_to_store(console)
    except Exception as e:
        logger.debug('Detailed stack trace info: %s', traceback.format_exc())
        console.print(f'Error migrating data from CSV file: {e}')

    console.print(
        Panel(
            dedent(
                '''
    [bold]Guides[/bold]:
    - Enter your text to start translating and building vocabulary
    - One sentence at a time, don't paste huge amounts of text at once
    - Get your vocabulary book file by running [bold]aivoc export --format csv[/bold]
    - Special Command:
        * [bold]no[/bold]: remove the last added word and start a manual selection
        * [bold]story[/bold]: Recall words by reading a story written by AI
        * [Ctrl+c] to quit'''
            ).strip(),
            title='Welcome to AI Vocabulary Builder!',
        )
    )
    while True:
        text = prompt(
            HTML('<tip>Enter text</tip><arrow>&gt;</arrow> '), style=prompt_style
        ).strip()
        if not text:
            continue
        elif text == COMMAND_NO:
            handle_cmd_no()
            continue
        elif text == COMMAND_STORY:
            LastActionResult.story_result = handle_cmd_story()
            continue

        LastActionResult.trans_result = handle_cmd_trans(text.strip())


MIN_LENGTH_TRANS_TEXT = 12


def handle_cmd_trans(text: str) -> TransActionResult:
    """Write a new word to the vocabulary book

    :param csv_book_path: The path of vocabulary book
    """
    if len(text) < MIN_LENGTH_TRANS_TEXT:
        console.print(
            f'Content too short, input at least {MIN_LENGTH_TRANS_TEXT} characters to start a translation.',
        )
        return TransActionResult(
            input_text=text, stored_to_voc_book=False, error='input_too_short'
        )
    mastered_word_s = get_mastered_word_store()
    word_store = get_word_store()

    progress = Progress(SpinnerColumn(), TextColumn("[bold blue] Querying OpenAI API"))
    orig_words = tokenize_text(text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = word_store.filter(orig_words) | mastered_word_s.filter(orig_words)
    with progress:
        task_id = progress.add_task("get", start=False)
        try:
            trans_ret = get_word_and_translation(text, known_words)
        except OpenAIServiceError as e:
            console.print(f'[red] Error processing text, detail: {e}[red]')
            logger.debug('Detailed stack trace info: %s', traceback.format_exc())
            return TransActionResult(
                input_text=text, stored_to_voc_book=False, error='openai_svc_error'
            )
        finally:
            progress.update(task_id, total=1, advance=1)

    word = trans_ret.word_sample
    console.print(f'> [bold]中文翻译：[/bold]{word.translated_text}\n')
    console.print(f'> The word AI has chosen is "[bold]{word.word}[/bold]".\n')

    try:
        validate_result_word(word, text)
    except WordInvalidForAdding as e:
        console.print(f'Unable to add "{word.word}", reason: {e}', style='red')
        return TransActionResult(
            input_text=text,
            stored_to_voc_book=False,
            error=str(e),
            word_sample=word,
            invalid_for_adding=True,
        )

    console.print(format_single_word(word))
    word_store.add(word)
    console.print(
        (
            f'[bold]"{word.word}"[/bold] was added to your vocabulary book ([bold]{word_store.count()}[/bold] '
            'in total), well done!\n'
        ),
        style='grey42',
    )
    return TransActionResult(input_text=text, stored_to_voc_book=True, word_sample=word)


def handle_cmd_no() -> NoActionResult:
    """Handle the "no" command, do following things:

    - Remove the last added word, also mark it as "mastered"
    - Let the user choose unknown word manually

    :return: The action result object.
    """
    ret = LastActionResult.trans_result
    if not (ret and ret.word_sample and (ret.stored_to_voc_book or ret.invalid_for_adding)):
        console.print(
            'The "no" command was used to remove the last added word and select the word manually.'
        )
        console.print('Can\'t get the last added word, please start a new translation first.')
        return NoActionResult(error='last_trans_absent')

    selector = ManuallySelector()
    if not ret.invalid_for_adding:
        selector.discard_word(ret.word_sample)

    progress = Progress(SpinnerColumn(), TextColumn("[bold blue] Querying OpenAI API"))
    with progress:
        task_id = progress.add_task("get", start=False)
        try:
            choices = selector.get_choices(ret.input_text)
        except OpenAIServiceError as e:
            console.print(f'[red] Error processing text, detail: {e}[red]')
            logger.debug('Detailed stack trace info: %s', traceback.format_exc())
            return NoActionResult(error='openai_svc_error')
        finally:
            progress.update(task_id, total=1, advance=1)

    if not choices:
        console.print('No words could be extracted from the text you given, skip.', style='grey42')
        return NoActionResult(error='no_choices_error')

    choice = selector.get_user_word_selection(choices)
    if not choice:
        console.print('Skipped.', style='grey42')
        return NoActionResult(error='user_skip')

    word_sample = WordSample(
        word=choice.word,
        word_normal=choice.word_normal,
        word_meaning=choice.word_meaning,
        pronunciation=choice.pronunciation,
        translated_text=ret.word_sample.translated_text,
        orig_text=ret.input_text,
    )

    try:
        validate_result_word(word_sample, ret.input_text)
    except WordInvalidForAdding as e:
        console.print(f'Unable to add "{word_sample.word}", reason: {e}', style='grey42')
        return NoActionResult(word=word_sample, stored_to_voc_book=False, error=str(e))

    word_store = get_word_store()
    word_store.add(word_sample)
    console.print(
        (
            f'[bold]"{word_sample.word}"[/bold] was added to your vocabulary book ([bold]{word_store.count()}[/bold] '
            'in total), well done!\n'
        ),
        style='grey42',
    )

    LastActionResult.trans_result = None
    return NoActionResult(word=word_sample, stored_to_voc_book=True)


class ManuallySelector:
    """A class dealing with manually word selection"""

    choice_skip = 'None of above, skip for now.'

    def discard_word(self, word: WordSample):
        """Discard a word added before"""
        # Remove last word, mark as mastered
        console.print(f'"{word.word}" was discarded, preparing other words...', style='grey42')
        get_word_store().remove(word.word)
        get_mastered_word_store().add(word.word)

    def get_choices(self, text: str) -> List[WordChoice]:
        """Get word choices from OpenAI service"""
        orig_words = tokenize_text(text)
        # Words already in vocabulary book and marked as mastered are treated as "known"
        known_words = get_word_store().filter(orig_words) | get_mastered_word_store().filter(
            orig_words
        )
        return get_word_choices(text, known_words)

    def get_user_word_selection(self, choices: List[WordChoice]) -> Optional[WordChoice]:
        """Get the word which the user selected

        :return: None if user give up selection
        """
        # Read user input
        str_choices = [w.get_console_display() for w in choices] + [self.choice_skip]
        answer = self.prompt_select_word(str_choices)
        if answer == self.choice_skip:
            return None

        # Get the WordChoice, turn it into WordSample and save to vocabulary book
        word_choice = next(w for w in choices if w.word == WordChoice.extract_word(answer))
        return word_choice

    def prompt_select_word(self, str_choices: List[str]) -> str:
        return questionary.select("Choose the word you don't know", choices=str_choices).ask()


DEFAULT_WORDS_CNT_FOR_STORY = 6


def handle_cmd_story(words_cnt: int = DEFAULT_WORDS_CNT_FOR_STORY) -> StoryActionResult:
    """Handle the "story" command, do following things:

    - Pick 6 words from the vocabulary book, use LRU algo
    - Write a story use those words

    :param words_cnt: The number of words used for writing the story
    :return: A story action result.
    """
    word_store = get_word_store()
    words = word_store.pick_story_words(words_cnt)
    if len(words) < words_cnt:
        console.print(
            (
                'Current number of words in your vocabulary book is less than {}.\n'
                'Translate more and come back later!'
            ).format(words_cnt),
            style='red',
        )
        return StoryActionResult(error='not_enough_words')

    # Call OpenAI service to get story text, word's normal form is preferred
    words_str = [w.get_normal_word_display() or w.word for w in words]
    console.print('Words for generating story: [bold]{}[/bold]'.format(', '.join(words_str)))
    progress = Progress(
        SpinnerColumn(), TextColumn("[bold blue] Querying OpenAI API to write the story...")
    )
    with progress:
        task_id = progress.add_task("get", start=False)
        try:
            story_text = get_story(words)
        except OpenAIServiceError as e:
            console.print(f'[red] Error retrieving story, detail: {e}[red]')
            logger.debug('Detailed stack trace info: %s', traceback.format_exc())
            return StoryActionResult(error='openai_svc_error')
        finally:
            progress.update(task_id, total=1, advance=1)

    # Display the story and update words to make LRU work
    console.print(Panel(highlight_story_text(story_text), title='Enjoy your reading'))
    word_store.update_story_words(words)

    # Display words on demand
    cmd_obj = StoryCmd(words_cnt)
    if cmd_obj.prompt_view_words():
        console.print(format_words(words))

    return StoryActionResult(words=words)


class StoryCmd:
    """Command class for "story" action.

    :param words_cnt: The number of words used for writing the story
    """

    def __init__(self, words_cnt: int):
        self.word_cnt = words_cnt

    def prompt_view_words(self) -> bool:
        return questionary.confirm("Do you want to view the meaning of these words?").ask()


def validate_result_word(word: WordSample, orig_text: str):
    """Check if a result word is valid before it can be put into vocabulary book"""
    if get_word_store().exists(word.word):
        raise WordInvalidForAdding('already in your vocabulary book')
    if get_mastered_word_store().exists(word.word):
        raise WordInvalidForAdding('already mastered')
    if word.word not in orig_text.lower():
        raise WordInvalidForAdding('not in the original text')


def format_words(words: List[WordSample]) -> Table:
    """Format a list of words as a rich table"""
    table = Table(title='生词详情', show_header=True)
    table.add_column("单词")
    table.add_column("发音")
    table.add_column("释义", overflow='fold', max_width=24)
    table.add_column("历史例句 / 翻译", overflow='fold')
    for w in words:
        table.add_row(
            w.word,
            w.pronunciation,
            w.get_word_meaning_display(),
            highlight_words(w.orig_text, [w.word]) + '\n' + w.translated_text,
        )
    return table


def format_single_word(word: WordSample) -> Table:
    """Format a single word sample

    :parm word: The word sample object
    """
    table = Table(title="", show_header=True)
    table.add_column("单词")
    table.add_column("发音")
    table.add_column("释义", overflow='fold')
    table.add_row(word.word, word.pronunciation, word.get_word_meaning_display())
    return table
