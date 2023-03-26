"""Main entrance of AI Vocabulary Builder"""
import logging
import sys
from typing import List, Optional

import click
import openai
from rich.console import Console

from voc_builder import __version__
from voc_builder.commands.export import FormatType, handle_export
from voc_builder.commands.remove import handle_remove
from voc_builder.interactive import enter_interactive_mode, handle_cmd_trans

# Set logging to stdout by default
log_format = "%(asctime)s - %(name)s - [%(levelname)s]:  %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)

logger = logging.getLogger()

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        return run()


@main.command(help='Show version info')
def version():
    console = Console()
    console.print(
        'Welcome to use "AI vocabulary builder", this is a product made by [bold]@piglei[/bold] with love.'
    )
    console.print(f'Version: {__version__}')


@main.command(help='Start the interactive shell')
@click.option('--api-key', envvar='OPENAI_API_KEY', required=True, help='Your OpenAI API key')
@click.option(
    '--api-base', envvar='OPENAI_API_BASE', required=False, help='The OpenAI API base address'
)
@click.option('--text', type=str, help='Text to be translated, interactive mode also supported')
@click.option(
    '--log-level', type=str, default='INFO', help='Log level, change it to DEBUG to see more logs'
)
def run(api_key: str, text: str, log_level: str, api_base: Optional[str] = None):
    # Set logging level
    logger.setLevel(getattr(logging, log_level.upper()))

    openai.api_key = api_key
    # Set the API base address if given
    if api_base:
        openai.api_base = api_base

    # Read text either from command line or stdin
    if text:
        handle_cmd_trans(text.strip())
        return
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
        handle_cmd_trans(text.strip())
        return

    # No text found, enter interactive mode
    enter_interactive_mode()


@main.command(help='Export current vocabulary book to file, support multiple formats')
@click.option(
    '--format',
    type=click.Choice([t.value for t in FormatType]),
    default=FormatType.ASCII.value,
    help='The format type, supported value: ascii, csv.',
)
@click.option(
    '--file-path',
    type=click.Path(),
    required=False,
    help='The file path to store the vocabulary file, will write to stdout if not provided.',
)
def export(format: str, file_path: Optional[str]):
    handle_export(format, file_path)


@main.command(help='Remove words from your vocabulary book')
@click.option(
    '--hard-remove',
    type=bool,
    default=False,
    help='Only perform remove, do not mark the deleted words into "mastered words"(the default behaviour)',
)
@click.argument('words', nargs=-1)
def remove(hard_remove: bool, words: List[str]):
    handle_remove(words, hard_remove)


if __name__ == '__main__':
    main()
