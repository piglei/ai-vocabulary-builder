from unittest import mock

import pytest

from voc_builder.exceptions import WordInvalidForAdding
from voc_builder.interactive import handle_cmd_trans, validate_result_word
from voc_builder.models import WordSample
from voc_builder.store import get_mastered_word_store, get_word_store

# A valid OpenAI reply example for text translating
OPENAI_REPLY_QUERY = 'word: world\npronunciation: wɔːld\nmeaning: 世界\ntranslated: 你好，世界。'


class TestCmdTrans:
    def test_known_words(self, tmp_path):
        """Check if known words from all sources works"""
        # Update known words from both sources
        get_word_store().add(WordSample.make_empty('foo'))
        get_mastered_word_store().add('baz')

        with mock.patch('voc_builder.openai_svc.query_openai') as mocked_query:
            mocked_query.return_value = OPENAI_REPLY_QUERY
            handle_cmd_trans("foo bar baz!")
            mocked_query.assert_called_once_with("foo bar baz!", {'foo', 'baz'})


# TODO: Test cmd no


def test_validate_result_word_misc(tmp_path):
    word_store = get_word_store()
    validate_result_word(WordSample.make_empty('foo'), 'foo bar')

    with pytest.raises(WordInvalidForAdding, match='already in your vocabulary book'):
        word_store.add(WordSample.make_empty('foo'))
        validate_result_word(WordSample.make_empty('foo'), 'foo bar')
    word_store.remove('foo')

    with pytest.raises(WordInvalidForAdding, match='already mastered'):
        get_mastered_word_store().add('foo')
        validate_result_word(WordSample.make_empty('foo'), 'foo bar')
    get_mastered_word_store().remove('foo')

    with pytest.raises(WordInvalidForAdding, match='not in the original text'):
        validate_result_word(WordSample.make_empty('foo'), 'bar baz')
