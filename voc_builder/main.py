"""Main entrance of AI Vocabulary Builder"""

import logging
import threading
import time
import webbrowser
from typing import Optional

import click
import requests
import uvicorn
from rich.console import Console

from voc_builder import __version__
from voc_builder.commands.export import FormatType, handle_export

# Set logging to stdout by default
log_format = "%(asctime)s - %(name)s - [%(levelname)s]:  %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)

logger = logging.getLogger()

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        return version()
    return None


@main.command(help="Show version info")
def version():
    console = Console()
    console.print(
        'Welcome to use "AI vocabulary builder", this is a product made by [bold]@piglei[/bold] with love.'
    )
    console.print(f"Version: {__version__}")


@main.command(help="Export current vocabulary book to file, support multiple formats")
@click.option(
    "--format",
    type=click.Choice([t.value for t in FormatType]),
    default=FormatType.CSV.value,
    help="The format type, supported value: ascii, csv.",
)
@click.option(
    "--file-path",
    type=click.Path(),
    required=False,
    help="The file path to store the vocabulary file, will write to stdout if not provided.",
)
def export(format: str, file_path: Optional[str]):
    handle_export(format, file_path)


@main.command(help="Start the notebook server")
@click.option(
    "--log-level",
    type=str,
    default="INFO",
    help="Log level, change it to DEBUG to see more logs",
)
@click.option(
    "--host", type=str, default="127.0.0.1", help="The host of notebook server"
)
@click.option("--port", type=int, default=16093, help="The host of notebook server")
def notebook(
    log_level: str,
    host: str,
    port: int,
):
    # Set logging level
    logger.setLevel(getattr(logging, log_level.upper()))

    def _open_in_browser():
        """Open the notebook in browser"""
        retries = 0
        addr = f"http://{host}:{port}"
        while retries < 10:
            time.sleep(1)
            try:
                requests.get(addr)
            except requests.exceptions.RequestException:
                retries += 1
                continue

            webbrowser.open(addr)
            break

    threading.Thread(target=_open_in_browser, daemon=True).start()

    print("Starting the notebook server...")
    uvicorn.run(
        "voc_builder.notepad.server:app",
        host=host,
        port=port,
        log_level=log_level.lower(),
        reload=False,
        workers=2,
    )


if __name__ == "__main__":
    main()
