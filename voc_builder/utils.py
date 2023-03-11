"""Basic utils for string and other simple types"""
import re
from typing import Sequence, Set


def tokenize_text(text: str) -> Set[str]:
    """Return all words in the given text, words are in lower case"""
    return {s.group().lower() for s in re.finditer(r'[a-zA-Z]+', text)}


def highlight_words(text: str, words: Sequence[str], extra_style: str = '') -> str:
    """Find all occurrences of the given words in text, make them highlighted"""
    pattern = r'\b({})\b'.format('|'.join(words))
    tag_start, tag_end = '[bold][underline]', '[/underline][/bold]'
    if extra_style:
        tag_start = f'{tag_start}[{extra_style}]'
        tag_end = f'[/{extra_style}]{tag_end}'
    return re.sub(pattern, rf'{tag_start}\1{tag_end}', text, flags=re.IGNORECASE)


def highlight_story_text(text: str) -> str:
    """Find all special words in the story text, make them highlighted.
    All special words are in this format: "${...}$"
    """
    pattern = r'\${?([\w-]*?)}?\$'
    return re.sub(pattern, r'[bold][underline]\1[/underline][/bold]', text, flags=re.IGNORECASE)
