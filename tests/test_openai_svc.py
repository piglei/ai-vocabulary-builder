import pytest

from voc_builder.models import WordSample
from voc_builder.openai_svc import parse_openai_reply


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
