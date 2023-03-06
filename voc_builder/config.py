"""Store configuration for project"""
from pathlib import Path

# Testings should patch these variables
#
# The default path for storing the vocabulary book
DEFAULT_CSV_FILE_PATH = Path('~/aivoc_builder.csv').expanduser()
# The default path for storing db files
DEFAULT_DB_PATH = Path('~/.aivoc_db').expanduser()
