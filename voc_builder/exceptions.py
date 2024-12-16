class VocBuilderError(Exception):
    """Base exception type for aivoc."""


class AIServiceError(VocBuilderError):
    """Error when calling OpenAI Services or parsing results from OpenAI"""


class AIModelNotConfiguredError(VocBuilderError):
    """Error when AI model is not configured properly."""


class WordInvalidForAdding(VocBuilderError):
    """Raised when a word sample is invalid for adding into vocabulary book"""
