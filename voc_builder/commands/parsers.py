"""Command parsers, mostly interactive commands."""
from dataclasses import dataclass
from typing import Optional

from .exceptions import CommandSyntaxError, NotCommandError


@dataclass
class ListCommandExpr:
    """The "list" command expression.

    :param num: The number of words to list.
    :param all: Whether to list all words.
    """

    num: Optional[int] = None
    all: bool = False


class ListCmdParser:
    """Parse the "list" command"""

    def parse(self, cmd: str) -> ListCommandExpr:
        """Parse the "list" command.

        :param cmd: The command to parse.
        :return: The parsed command expression.
        :raise: NotCommandError if the given input is not a command;
            CommandSyntaxError if the command syntax is invalid.
        """
        tokens = cmd.strip().split()
        if not (len(tokens) <= 2 and tokens[0] == 'list'):
            raise NotCommandError()

        # Pattern: list all, return the command with default arguments
        if len(tokens) == 1:
            return ListCommandExpr()

        str_arg = tokens[1]
        # Pattern: list all
        if str_arg == 'all':
            return ListCommandExpr(all=True)

        # Pattern: list <num>
        try:
            num = int(str_arg)
        except ValueError:
            raise CommandSyntaxError(f'limit not a number: {str_arg}')
        if num <= 0:
            raise CommandSyntaxError('the limit number must be positive.')
        return ListCommandExpr(num=num)
