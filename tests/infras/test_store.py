import importlib
import os
import time
from dataclasses import asdict
from pathlib import Path

from tinydb import Query

from voc_builder.builder.models import WordProgress, WordSample
from voc_builder.infras import config
from voc_builder.infras.store import (
    InternalStateStore,
    MasteredWordStore,
    SystemSettingsStore,
    WordStore,
)
from voc_builder.system.models import GeminiConfig, OpenAIConfig, SystemSettings


class TestMasteredWordsStore:
    def test_filter(self, tmp_path):
        mastered_words_s = MasteredWordStore(tmp_path / "foo.json")
        mastered_words_s.add("program")
        mastered_words_s.add("python")
        assert mastered_words_s.filter({"foo", "python", "bar"}) == {"python"}

    def test_repeated_add(self, tmp_path):
        mastered_words_s = MasteredWordStore(tmp_path / "foo.json")
        mastered_words_s.add("program")
        mastered_words_s.add("program")
        mastered_words_s.add("python")
        assert set(mastered_words_s.all()) == {"python", "program"}

    def test_exists(self, tmp_path):
        mastered_words_s = MasteredWordStore(tmp_path / "foo.json")
        assert mastered_words_s.exists("program") is False
        mastered_words_s.add("program")
        assert mastered_words_s.exists("program") is True

    def test_remove(self, tmp_path):
        mastered_words_s = MasteredWordStore(tmp_path / "foo.json")
        mastered_words_s.add("program")
        assert mastered_words_s.exists("program") is True
        mastered_words_s.remove("program")
        assert mastered_words_s.exists("program") is False


class TestWordStore:
    def test_get(self, tmp_path):
        word_store = WordStore(tmp_path / "foo.json")
        word_store.add(WordSample.make_empty("program"))
        obj = word_store.get("program")
        assert obj
        assert obj.word == "program"

    def test_misc(self, tmp_path):
        word_store = WordStore(tmp_path / "foo.json")
        word_store.add(WordSample.make_empty("program"))
        word_store.add(WordSample.make_empty("program"))
        word_store.add(WordSample.make_empty("python"))
        assert word_store.count() == 2
        assert list(word_store.all())[0].word == "program"

        word_store.remove("program")
        assert word_store.count() == 1

    def test_list_latest(self, tmp_path):
        word_store = WordStore(tmp_path / "foo.json")
        for i in range(50):
            word_store.add(WordSample.make_empty(f"word{i}"))

        items = word_store.list_latest(limit=10)
        # The items should starts from "word40"
        for i, word in enumerate(items):
            assert word.word == f"word{i+40}"

        # Test list all
        assert len(word_store.list_latest()) == 50

    def test_story_words(self, tmp_path):
        word_store = WordStore(tmp_path / "foo.json")
        for s in "Python program language is easy to read and write".split():
            word_store.add(WordSample.make_empty(s))

        words = word_store.pick_story_words(count=1)
        assert len(words) == 1
        word_store.update_story_words(words)
        first_word = words[0]

        # Check the status was updated
        obj = word_store.get(first_word.word)
        assert obj
        assert obj.wp.storied_cnt == 1
        assert obj.wp.ts_date_storied is not None

        # Now the `pick_story_words` call should return a different word
        new_words = word_store.pick_story_words(count=1)
        assert new_words[0] != first_word

    def test_filter(self, tmp_path):
        word_store = WordStore(tmp_path / "foo.json")
        word_store.add(WordSample.make_empty("program"))
        word_store.add(WordSample.make_empty("python"))
        assert word_store.filter({"foo", "python", "bar"}) == {"python"}

    def test_search(self, tmp_path):
        word_store = WordStore(tmp_path / "foo.json")
        word_store.add(WordSample.make_empty("program"))
        word_store.add(WordSample.make_empty("python"))
        # Search is case insensitive
        assert list(word_store.search("Py"))[0].ws.word == "python"


class TestDifferentWordVersion:
    """Test if the word store is able to handle data in legacy versions"""

    def test_get_without_word_normal_form(self, tmp_path):
        """Test word without "word_normal_form" field(version <= 0.2.0)"""
        word_store = WordStore(tmp_path / "foo.json")
        Word = Query()
        data = {
            "word": "program",
            "word_meaning": "",
            "pronunciation": "",
            "orig_text": "",
            "translated_text": "",
        }
        word_store._db.upsert(
            {
                "ws": data,
                "wp": asdict(WordProgress(word=data["word"])),
                "ts_date_added": time.time(),
            },
            Word.ws.word == data["word"],
        )
        obj = word_store.get("program")
        assert obj
        assert obj.word == "program"
        assert len(list(word_store.all())) == 1


class TestInternalStateStore:
    def test_state(self, tmp_path):
        state_store = InternalStateStore(tmp_path / "foo.json")
        state = state_store.get_internal_state()
        assert state is not None
        assert state.last_ver_checking_ts == -1

        state.last_ver_checking_ts = time.time()
        state_store.set_internal_state(state)
        state = state_store.get_internal_state()
        assert state.last_ver_checking_ts > 0


class TestSysSettingsStore:
    def test_system_settings(self, tmp_path):
        store = SystemSettingsStore(tmp_path / "foo.json")
        assert store.get_system_settings() is None

        settings = SystemSettings(
            model_provider="openai",
            openai_config=OpenAIConfig(
                api_key="test_key", api_host="test_host", model="gtp-4o"
            ),
            gemini_config=GeminiConfig(api_key="", api_host="", model=""),
        )
        store.set_system_settings(settings)
        saved_settings = store.get_system_settings()

        assert saved_settings == settings


class TestStoreDir:
    def test_mocked_location(self, tmp_path):
        assert config.DEFAULT_DB_PATH == tmp_path
        assert config.DEFAULT_CSV_FILE_PATH == tmp_path / "foo.csv"

    def test_data_dir_location(self, monkeypatch, tmp_path):
        # Set the environment variable to a test value
        monkeypatch.setenv("AIVOC_DATA_DIR", str(tmp_path))

        # Reload the module to pick up the new environment variable value
        importlib.reload(config)

        data_dir = Path(os.environ["AIVOC_DATA_DIR"]).expanduser()
        assert config.DEFAULT_DB_PATH == data_dir / ".aivoc_db"
        assert config.DEFAULT_CSV_FILE_PATH == data_dir / "aivoc_builder.csv"
        importlib.reload(config)

        data_dir = Path(os.environ["AIVOC_DATA_DIR"]).expanduser()
        assert config.DEFAULT_DB_PATH == data_dir / ".aivoc_db"
        assert config.DEFAULT_CSV_FILE_PATH == data_dir / "aivoc_builder.csv"
