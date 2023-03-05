from unittest import mock

import pytest

from voc_builder.main import (
    VocBuilderCSVFile,
    WordInvalidForAdding,
    get_mastered_word_store,
    validate_result_word,
    write_new_one,
)
from voc_builder.models import WordSample


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    """Set up databases by changing the database path so no one get hurt."""
    with mock.patch('voc_builder.main.DEFAULT_DB_PATH', new=str(tmp_path)):
        yield


@pytest.fixture
def w_sample_world() -> WordSample:
    return WordSample('world', '世界', 'wɔrld', 'Hello, world!', '你好，世界！')


# A valid OpenAI reply example for text translating
OPENAI_REPLY_QUERY = 'word: world\npronunciation: wɔːld\nmeaning: 世界\ntranslated: 你好，世界。'


class TestWriteNewOne:
    def test_known_words(self, tmp_path):
        """Check if known words from all sources works"""
        csv_book_path = tmp_path / 'foo.csv'
        # Update known words from both sources
        builder = VocBuilderCSVFile(csv_book_path)
        builder.append_word(WordSample.make_empty('foo'))
        get_mastered_word_store().add('baz')

        with mock.patch('voc_builder.main.query_openai') as mocked_query:
            mocked_query.return_value = OPENAI_REPLY_QUERY
            write_new_one("foo bar baz!", csv_book_path=csv_book_path)
            mocked_query.assert_called_once_with("foo bar baz!", {'foo', 'baz'})


class TestVocBuilderCSVFile:
    def test_is_duplicated(self, tmp_path, w_sample_world):
        builder = VocBuilderCSVFile(tmp_path / 'foo.csv')
        assert builder.is_duplicated(w_sample_world) is False

        builder.append_word(w_sample_world)
        assert builder.is_duplicated(w_sample_world) is True

    def test_find_known_words(self, tmp_path, w_sample_world):
        builder = VocBuilderCSVFile(tmp_path / 'foo.csv')
        builder.append_word(w_sample_world)
        assert builder.find_known_words({'hello', 'world'}) == {'world'}

    def test_repeated_calls(self, tmp_path, w_sample_world):
        p = tmp_path / 'foo.csv'
        builder = VocBuilderCSVFile(p)
        builder.append_word(w_sample_world)

        words = builder.read_all()
        assert len(words) == 1
        assert words[0].word == 'world'
        assert words[0].word_meaning == '世界'
        assert words[0].translated_text == '你好，世界！'

        # re-initialize the obj and append another word
        builder_2 = VocBuilderCSVFile(p)
        builder_2.append_word(WordSample('hello', '你好', 'həˈlō', 'Hello.', '你好。'))

        words_2 = builder_2.read_all()
        assert len(words_2) == 2
        assert words_2[1].word == 'hello'
        assert words_2[1].word_meaning == '你好'
        assert words_2[1].translated_text == '你好。'

    def test_remove_word(self, tmp_path, w_sample_world):
        builder = VocBuilderCSVFile(tmp_path / 'foo.csv')
        builder.append_word(w_sample_world)
        builder.append_word(WordSample('hello', '你好', 'həˈlō', 'Hello.', '你好。'))
        assert len(builder.read_all()) == 2

        builder.remove_words({'world'})
        words = builder.read_all()
        assert len(words) == 1
        assert words[0].word == 'hello'


def test_validate_result_word_misc(tmp_path):
    builder = VocBuilderCSVFile(tmp_path / 'foo.csv')
    validate_result_word(WordSample.make_empty('foo'), 'foo bar', builder)

    with pytest.raises(WordInvalidForAdding, match='already in your vocabulary book'):
        builder.append_word(WordSample.make_empty('foo'))
        validate_result_word(WordSample.make_empty('foo'), 'foo bar', builder)
    builder.remove_words({'foo'})

    with pytest.raises(WordInvalidForAdding, match='already mastered'):
        get_mastered_word_store().add('foo')
        validate_result_word(WordSample.make_empty('foo'), 'foo bar', builder)
    get_mastered_word_store().remove('foo')

    with pytest.raises(WordInvalidForAdding, match='not in the original text'):
        validate_result_word(WordSample.make_empty('foo'), 'bar baz', builder)
