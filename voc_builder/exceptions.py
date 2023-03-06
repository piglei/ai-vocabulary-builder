class VocBuilderError(Exception):
    """Base exception type for aivoc."""


class WordInvalidForAdding(VocBuilderError):
    """Raised when a word sample is invalid for adding into vocabulary book"""
