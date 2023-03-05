import tempfile
from pathlib import Path

import pytest

from voc_builder.main import VocBuilderCSVFile, WordSample, parse_openai_reply


@pytest.fixture
def w_sample_world() -> WordSample:
    return WordSample('world', '世界', 'wɔrld', 'Hello, world!', '你好，世界！')


class TestVocBuilderCSVFile:
    def test_is_duplicated(self, w_sample_world):
        p = Path(tempfile.mktemp())
        builder = VocBuilderCSVFile(p)
        assert builder.is_duplicated(w_sample_world) is False

        builder.append_word(w_sample_world)
        assert builder.is_duplicated(w_sample_world) is True

    def test_find_known_words(self, w_sample_world):
        builder = VocBuilderCSVFile(Path(tempfile.mktemp()))
        builder.append_word(w_sample_world)
        assert builder.find_known_words('Hello, world') == ['world']

    def test_repeated_calls(self, w_sample_world):
        p = Path(tempfile.mktemp())
        builder = VocBuilderCSVFile(p)
        builder.append_word(w_sample_world)

        words = builder.read_all()
        assert len(words) == 1
        assert words[0].word == 'world'
        assert words[0].word_meaning == '世界'
        assert words[0].translated_text == '你好，世界！'

        # re-initialize the obj and append another word
        builder_2 = VocBuilderCSVFile(p)
        builder_2.append_word(WordSample('Hello', '你好', 'həˈlō', 'Hello.', '你好。'))

        words_2 = builder_2.read_all()
        assert len(words_2) == 2
        assert words_2[1].word == 'Hello'
        assert words_2[1].word_meaning == '你好'
        assert words_2[1].translated_text == '你好。'


@pytest.mark.parametrize(
    'orig_text,input,expected',
    [
        # A standard reply
        (
            'Hello, world.',
            'word: world\npronunciation: wɔːld\nmeaning: 世界\ntranslated: 你好，世界。',
            WordSample(
                word='world',
                pronunciation='wɔːld',
                word_meaning='世界',
                orig_text='Hello, world.',
                translated_text='你好，世界。',
            ),
        ),
        # A reply using non-standard key name
        (
            'Hello, world.',
            'Uncommon word: world\npronunciation: wɔːld\nmeaning: 世界\ntranslated: 你好，世界。',
            WordSample(
                word='world',
                pronunciation='wɔːld',
                word_meaning='世界',
                orig_text='Hello, world.',
                translated_text='你好，世界。',
            ),
        ),
        # A reply which has extra content in the beginning and the end
        (
            'Hello, world.',
            'foobar\n\nword: world\npronunciation: wɔːld\nmeaning: 世界\ntranslated: 你好，世界。\nother info',
            WordSample(
                word='world',
                pronunciation='wɔːld',
                word_meaning='世界',
                orig_text='Hello, world.',
                translated_text='你好，世界。',
            ),
        ),
        (
            'Hello, world.',
            'invalid reply',
            None,
        ),
    ],
)
def test_parse_openai_reply(orig_text, input, expected):
    if expected is None:
        with pytest.raises(ValueError):
            parse_openai_reply(input, orig_text)
    else:
        assert parse_openai_reply(input, orig_text) == expected
