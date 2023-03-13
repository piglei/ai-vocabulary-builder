"""Store configuration for project"""
import os
from pathlib import Path

# Testings should patch these variables
#
# The default path for storing the vocabulary book
data_dir = Path(os.environ.get('AIVOC_DATA_DIR', '~')).expanduser()
DEFAULT_CSV_FILE_PATH = data_dir / 'aivoc_builder.csv'
# The default path for storing db files
DEFAULT_DB_PATH = data_dir / '.aivoc_db'
