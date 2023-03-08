class VocBuilderError(Exception):
    """Base exception type for aivoc."""


class OpenAIServiceError(VocBuilderError):
    """Error when calling OpenAI Services or parsing results from OpenAI"""


class WordInvalidForAdding(VocBuilderError):
    """Raised when a word sample is invalid for adding into vocabulary book"""
