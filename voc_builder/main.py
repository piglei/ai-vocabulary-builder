"""Main entrance of AI Vocabulary Builder"""
import logging
import sys
from typing import Optional

import click
import openai

from voc_builder.commands.export import FormatType, handle_export
from voc_builder.interactive import enter_interactive_mode, handle_cmd_trans

# Set logging to stdout by default
log_format = "%(asctime)s - %(name)s - [%(levelname)s]:  %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)

logger = logging.getLogger()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        return run()


@main.command(help='Start the interactive shell')
@click.option('--api-key', envvar='OPENAI_API_KEY', required=True, help='Your OpenAI API key')
@click.option('--text', type=str, help='Text to be translated, interactive mode also supported')
@click.option(
    '--log-level', type=str, default='INFO', help='Log level, change it to DEBUG to see more logs'
)
def run(api_key: str, text: str, log_level: str):
    # Set logging level
    logger.setLevel(getattr(logging, log_level.upper()))

    openai.api_key = api_key

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


if __name__ == '__main__':
    main()
