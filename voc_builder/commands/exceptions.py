class CommandParseError(Exception):
    """Exception raised when there is a command parse error."""


class NotCommandError(CommandParseError):
    """Exception raised when given input is not a command."""


class CommandSyntaxError(CommandParseError):
    """Exception raised when a command syntax is invalid."""
