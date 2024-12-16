import pytest

from voc_builder import config
from voc_builder.models import WordSample


@pytest.fixture(autouse=True)
def setup_config(tmp_path):
    """Set up configs, change the path of databases and book so no one get hurt."""
    config.DEFAULT_DB_PATH = tmp_path
    config.DEFAULT_CSV_FILE_PATH = tmp_path / "foo.csv"


@pytest.fixture
def w_sample_world() -> WordSample:
    return WordSample(
        "world",
        "world",
        definitions=["世界"],
        pronunciation="wɔrld",
        orig_text="Hello, world!",
        translated_text="你好，世界！",
    )
