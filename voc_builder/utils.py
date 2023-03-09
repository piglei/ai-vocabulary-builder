"""Basic utils for string and other simple types"""
import re
from typing import Sequence, Set


def tokenize_text(text: str) -> Set[str]:
    """Return all words in the given text, words are in lower case"""
    return {s.group().lower() for s in re.finditer(r'[a-zA-Z]+', text)}


def highlight_words(text: str, words: Sequence[str]) -> str:
    """Find all occurrences of the given words in text, make them highlighted"""
    pattern = r'\b({})\b'.format('|'.join(words))
    return re.sub(pattern, r'[bold][underline]\1[/underline][/bold]', text, flags=re.IGNORECASE)


def highlight_story_text(text: str) -> str:
    """Find all special words in the story text, make them highlighted.
    All special words are in this format: "$${...}$$"
    """
    pattern = r'\$\${?(.*?)}?\$\$'
    return re.sub(pattern, r'[bold][underline]\1[/underline][/bold]', text, flags=re.IGNORECASE)
