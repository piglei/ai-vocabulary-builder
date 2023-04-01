"""Remove words from vocabulary book."""
from itertools import islice

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console

from voc_builder.store import get_mastered_word_store, get_word_store

console = Console()


class WordCompleter(Completer):
    """A completer that completes words from the word store."""

    # The maximum number of completions to show.
    limit = 1000

    def get_completions(self, document, complete_event):
        """Search the word store for words that match the input word. A fuzzy search
        is used."""
        word = document.get_word_before_cursor()
        for item in islice(get_word_store().search(keyword=word), self.limit):
            display = HTML(item.ws.word.replace(word, f'<b>{word}</b>'))
            display_meta = HTML(
                f'{item.ws.get_word_meaning_display()} | {item.date_added_diff_for_humans}'
            )
            yield Completion(
                item.ws.word,
                start_position=-len(word),
                display=display,
                display_meta=display_meta,
            )


prompt_style = Style.from_dict(
    {
        "tip": "bold yellow",
        "arrow": "bold",
    }
)


def handle_cmd_remove():
    """Handle the "remove" command in the interactive mode."""

    def bottom_toolbar():
        """Show some meta info in the bottom toolbar."""
        return HTML(
            'Input "q" to quit | Words in total: <b>{}</b>'.format(get_word_store().count())
        )

    session = PromptSession(completer=WordCompleter())  # type: ignore
    while True:

        def pre_run():
            # Show auto completer without pressing any keys
            session.app.current_buffer.start_completion()

        words = session.prompt(
            HTML('<tip>Input word to be removed</tip><arrow> -&gt;</arrow> '),
            style=prompt_style,
            pre_run=pre_run,
            mouse_support=True,
            bottom_toolbar=bottom_toolbar,
        )
        words = words.strip()
        if not words or words == 'q':
            return

        for w in words.split():
            remove_word(w)


def remove_word(w: str):
    """Remove a word from the vocabulary book and print the result to the console.

    :param w: the word to be removed
    """
    word_store = get_word_store()
    mword_store = get_mastered_word_store()
    w_ret = word_store.remove(w)
    m_ret = mword_store.remove(w)
    if w_ret:
        console.print(f'[bold]"{w}"[/bold] has been removed.', style='blue')
    elif m_ret:
        console.print(f'[bold]"{w}"[/bold] has been removed form "mastered words".', style='blue')
    else:
        console.print(f'[bold]"{w}"[/bold] not found.', style='red')
