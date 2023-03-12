"""Store configuration for project"""
import os
from pathlib import Path

# Testings should patch these variables
#
# The default path for storing the vocabulary book
aivoc_home = os.environ.get("AIVOC_HOME", "~")
DEFAULT_CSV_FILE_PATH = Path(f"{aivoc_home}/aivoc_builder.csv").expanduser()
# The default path for storing db files
DEFAULT_DB_PATH = Path(f"{aivoc_home}/.aivoc_db").expanduser()
