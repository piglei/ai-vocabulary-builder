"""Store configuration for project"""
import os
from pathlib import Path

# Testings should patch these variables
#
# The default path for storing the vocabulary book
data_dir = os.environ.get('AIVOC_DATA_DIR', '~')
if data_dir.endswith('/'):
    data_dir = data_dir[:-1]

DEFAULT_CSV_FILE_PATH = Path(f'{data_dir}/aivoc_builder.csv').expanduser()
# The default path for storing db files
DEFAULT_DB_PATH = Path(f'{data_dir}/.aivoc_db').expanduser()
