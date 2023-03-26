import pytest

from voc_builder.commands.exceptions import CommandSyntaxError, NotCommandError
from voc_builder.commands.parsers import ListCmdParser, ListCommandExpr


class TestListCmdParser:
    @pytest.mark.parametrize(
        'cmd,ret',
        [
            ('list', ListCommandExpr()),
            ('list all', ListCommandExpr(all=True)),
            ('list 25', ListCommandExpr(num=25)),
        ],
    )
    def test_parse(self, cmd, ret):
        assert ListCmdParser().parse(cmd) == ret

    @pytest.mark.parametrize(
        'cmd,exc_type',
        [
            ('invalid_without_space', NotCommandError),
            ('list is a common english word.', NotCommandError),
            ('list -1', CommandSyntaxError),
            ('list not_a_number', CommandSyntaxError),
        ],
    )
    def test_parse_error(self, cmd, exc_type):
        with pytest.raises(exc_type):
            ListCmdParser().parse(cmd)
