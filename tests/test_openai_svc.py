import pytest

from voc_builder.models import WordChoice, WordSample
from voc_builder.openai_svc import parse_openai_reply, parse_word_choices_reply


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
            'unknown-word: world\npronunciation: wɔːld\nmeaning: 世界\ntranslated: 你好，世界。',
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


@pytest.mark.parametrize(
    'input,expected',
    [
        # A standard reply
        (
            '\n\nword: versions\npronunciation: /\u02c8v\u0259r\u0292\u0259nz/\nmeaning: \u7248\u672c\n\nword: ambiguous\npronunciation: /\u00e6m\u02c8b\u026a\u0261ju\u0259s/\nmeaning: \u6a21\u68f1\u4e24\u53ef\u7684\n\nword: nested\npronunciation: /\u02c8n\u025bst\u026ad/\nmeaning: \u5d4c\u5957\u7684',  # noqa: E501
            [
                WordChoice(word='versions', word_meaning='版本', pronunciation='/ˈvərʒənz/'),
                WordChoice(word='ambiguous', word_meaning='模棱两可的', pronunciation='/æmˈbɪɡjuəs/'),
                WordChoice(word='nested', word_meaning='嵌套的', pronunciation='/ˈnɛstɪd/'),
            ],
        ),
        # A reply with non-standard key name
        (
            '\n\nUnknown-word: versions\npronunciation: /\u02c8v\u0259r\u0292\u0259nz/\nmeaning: \u7248\u672c',
            [
                WordChoice(word='versions', word_meaning='版本', pronunciation='/ˈvərʒənz/'),
            ],
        ),
        (
            'invalid reply',
            [],
        ),
    ],
)
def test_parse_word_choices_reply(input, expected):
    assert parse_word_choices_reply(input) == expected
