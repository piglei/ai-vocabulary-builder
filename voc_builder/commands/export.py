"""Handle export command"""

import sys
from enum import Enum
from typing import Optional

from rich.console import Console

from voc_builder.misc.export import VocCSVWriter

console = Console()


class FormatType(Enum):
    CSV = "csv"


def handle_export(format: str, file_path: Optional[str]):
    """Handle the export command

    :param format: The output format, e.g. "ascii", "csv".
    :param file_path: The file path where the output will be written, if not specified,
        use stdout
    """
    if format == FormatType.CSV.value:
        if file_path:
            with open(file_path, "w", encoding="utf-8") as fp:
                VocCSVWriter().write_to(fp)
                console.print(f'Exported to "{file_path}" successfully, format: csv.')
        else:
            VocCSVWriter().write_to(sys.stdout)
        return
