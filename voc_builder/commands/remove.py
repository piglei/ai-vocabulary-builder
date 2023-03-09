"""Handle remove command"""
from typing import List

from rich.console import Console

from voc_builder.store import get_mastered_word_store, get_word_store

console = Console()


def handle_remove(words: List[str], hard_remove: bool):
    """Handle the remove command

    :param words: Words need to be removed
    :param hard_remove: Whether to mark the word as "mastered" or remove entirely
    """
    word_store = get_word_store()
    mword_store = get_mastered_word_store()
    for w in words:
        if hard_remove:
            w_ret = word_store.remove(w)
            m_ret = mword_store.remove(w)
            if w_ret:
                console.print(f'[bold]"{w}"[/bold] has been removed.', style='blue')
            elif m_ret:
                console.print(
                    f'[bold]"{w}"[/bold] has been removed form "mastered words".', style='blue'
                )
            else:
                console.print(f'[bold]"{w}"[/bold] not found.', style='red')
            continue

        w_ret = word_store.remove(w)
        if w_ret:
            mword_store.add(w)
            console.print(
                f'[bold]"{w}"[/bold] has been removed from the vocabulary book, added to "mastered words.',
                style='blue',
            )
        else:
            console.print(f'[bold]"{w}"[/bold] not found.', style='red')
