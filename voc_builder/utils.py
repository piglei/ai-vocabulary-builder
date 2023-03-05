"""Basic utils for string and other simple types"""
import re
from typing import Set


def tokenize_text(text: str) -> Set[str]:
    """Return all words in the given text, words are in lower case"""
    return {s.group().lower() for s in re.finditer(r'[a-zA-Z]+', text)}
