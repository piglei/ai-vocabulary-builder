from unittest import mock

import pytest

from voc_builder.commands.parsers import ListCommandExpr
from voc_builder.exceptions import OpenAIServiceError, WordInvalidForAdding
from voc_builder.interactive import (
    LastActionResult,
    ManuallySelector,
    TransActionResult,
    handle_cmd_list,
    handle_cmd_no,
    handle_cmd_story,
    handle_cmd_trans,
    validate_result_word,
)
from voc_builder.models import WordChoice, WordSample
from voc_builder.store import get_mastered_word_store, get_word_store

# A valid OpenAI reply example for text translating
OPENAI_REPLY_QUERY = (
    'word: world\nnormal_form: world\npronunciation: wɔːld\nmeaning: 世界\ntranslated: 你好，世界。'
)


class TestCmdTrans:
    def test_input_length(self, tmp_path):
        ret = handle_cmd_trans("world")
        assert ret.error == 'input_length_invalid'

    def test_known_words(self, tmp_path):
        """Check if known words from all sources works"""
        with mock.patch('voc_builder.openai_svc.query_openai', side_effect=OpenAIServiceError()):
            ret = handle_cmd_trans("foo bar baz!")
            assert ret.stored_to_voc_book is False
            assert ret.error == 'openai_svc_error'

    def test_openai_svc_error(self, tmp_path):
        """Test when there's an error calling the OpenAI API"""
        with mock.patch('voc_builder.openai_svc.query_openai', side_effect=OpenAIServiceError()):
            ret = handle_cmd_trans("world foo bar baz!")
            assert ret.error == 'openai_svc_error'

    def test_normal(self, tmp_path):
        """Check if known words from all sources works"""
        # Update known words from both sources
        get_word_store().add(WordSample.make_empty('foo'))
        get_mastered_word_store().add('baz')

        with mock.patch('voc_builder.openai_svc.query_openai') as mocked_query:
            mocked_query.return_value = OPENAI_REPLY_QUERY
            ret = handle_cmd_trans("world foo bar baz!")

            assert mocked_query.call_args[0] == ("world foo bar baz!", {'foo', 'baz'})
            assert ret.stored_to_voc_book is True
            assert ret.word_sample and ret.word_sample.word == 'world'
            assert get_word_store().exists('world') is True


class TestCmdNo:
    @pytest.fixture
    def has_last_added_word(self):
        """Simulate that a new word has been added through last action"""
        word_foo = WordSample.make_empty('foo')
        with mock.patch.object(
            LastActionResult,
            'trans_result',
            TransActionResult(
                input_text='foo bar',
                stored_to_voc_book=True,
                word_sample=word_foo,
            ),
        ):
            yield

    def test_condition_not_met(self):
        ret = handle_cmd_no()
        assert ret.error == 'last_trans_absent'

    def test_word_invalid(self):
        """When the word is present but invalid for adding, also allows "no" action"""
        word_foo = WordSample.make_empty('foo')
        with mock.patch.object(
            LastActionResult,
            'trans_result',
            TransActionResult(
                input_text='foo bar',
                stored_to_voc_book=False,
                word_sample=word_foo,
                invalid_for_adding=True,
            ),
        ), mock.patch(
            'voc_builder.interactive.get_word_choices', side_effect=OpenAIServiceError()
        ):
            ret = handle_cmd_no()
            assert ret.error == 'openai_svc_error'

    def test_openai_svc_error(self, has_last_added_word):
        with mock.patch(
            'voc_builder.interactive.get_word_choices', side_effect=OpenAIServiceError()
        ) as mocker:
            ret = handle_cmd_no()
            assert get_word_store().exists('foo') is False
            assert ret.error == 'openai_svc_error'
            mocker.assert_called_once_with('foo bar', {'foo'})

    def test_no_choices_error(self, has_last_added_word):
        with mock.patch('voc_builder.interactive.get_word_choices', return_value=[]):
            ret = handle_cmd_no()
            assert ret.error == 'no_choices_error'

    def test_user_skip_error(self, has_last_added_word):
        with mock.patch(
            'voc_builder.interactive.get_word_choices',
            return_value=[
                WordChoice(word='bar', word_normal='bar', word_meaning='bar', pronunciation='')
            ],
        ), mock.patch(
            'voc_builder.interactive.ManuallySelector.prompt_select_word',
            return_value=ManuallySelector.choice_skip,
        ):
            ret = handle_cmd_no()
            assert ret.error == 'user_skip'

    def test_validate_error(self, has_last_added_word):
        with mock.patch(
            'voc_builder.interactive.get_word_choices',
            return_value=[
                WordChoice(word='bar', word_normal='bar', word_meaning='bar', pronunciation='')
            ],
        ), mock.patch(
            'voc_builder.interactive.ManuallySelector.prompt_select_word',
            return_value='bar',
        ):
            get_mastered_word_store().add('bar')
            ret = handle_cmd_no()
            assert ret.word and ret.word.word == 'bar'
            assert ret.error == 'already mastered'

    def test_normal(self, has_last_added_word):
        with mock.patch(
            'voc_builder.interactive.get_word_choices',
            return_value=[
                WordChoice(word='bar', word_normal='bar', word_meaning='bar', pronunciation='')
            ],
        ), mock.patch(
            'voc_builder.interactive.ManuallySelector.prompt_select_word',
            return_value='bar',
        ):
            ret = handle_cmd_no()
            assert get_word_store().exists('bar') is True
            assert ret.word and ret.word.word == 'bar'
            assert ret.stored_to_voc_book is True
            assert ret.error == ''
            assert LastActionResult.trans_result is None


class TestCmdStory:
    def test_not_enough_words(self):
        ret = handle_cmd_story()
        assert ret.error == 'not_enough_words'

    def test_openai_svc_error(self):
        get_word_store().add(WordSample.make_empty('foo'))
        with mock.patch('voc_builder.openai_svc.query_story', side_effect=IOError()) as mocker:
            ret = handle_cmd_story(1)
            assert ret.error == 'openai_svc_error'
            assert mocker.call_args[0][0] == ['foo']

    def test_normal(self):
        get_word_store().add(WordSample.make_empty('foo'))
        with mock.patch(
            'voc_builder.openai_svc.query_story', return_value='story text'
        ), mock.patch('voc_builder.interactive.StoryCmd.prompt_view_words', return_value=True):
            ret = handle_cmd_story(1)
            word = get_word_store().get('foo')

            assert word is not None
            assert word.wp.storied_cnt == 1
            assert len(ret.words) == 1
            assert ret.error == ''


class TestCmdList:
    @pytest.fixture(autouse=True)
    def _setup(self):
        """Set up the word store with 50 words"""
        for i in range(50):
            get_word_store().add(WordSample.make_empty(f'bar{i}'))

    def test_normal(self):
        ret = handle_cmd_list(ListCommandExpr(25))
        for i in range(25):
            assert ret.words[i].word == f'bar{i+25}'
        assert len(ret.words) == 25
        assert ret.error == ''

    def test_all_words(self):
        ret = handle_cmd_list(ListCommandExpr(all=True))
        assert len(ret.words) == 50
        assert ret.error == ''


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
