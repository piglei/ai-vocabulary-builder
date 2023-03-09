import pytest

from voc_builder.models import TranslationResult, WordChoice, WordSample
from voc_builder.openai_svc import parse_openai_reply, parse_word_choices_reply

word_sample_hello = WordSample(
    word='world',
    word_normal='world',
    pronunciation='wɔːld',
    word_meaning='世界',
    orig_text='Hello, world.',
    translated_text='你好，世界。',
)

_reply_standard = '''\
word: world
normal_form: world
pronunciation: wɔːld
meaning: 世界
translated: 你好，世界。'''

_reply_non_standard_key_name = '''\
unknown-word: world
normal_form: world
pronunciation: wɔːld
meaning: 世界
translated: 你好，世界。'''

_reply_with_extra_content = '''\
foobar

word: world
normal_form: world
pronunciation: wɔːld
meaning: 世界
translated: 你好，世界。
other info'''


@pytest.mark.parametrize(
    'orig_text,input,expected',
    [
        # A standard reply
        (
            'Hello, world.',
            _reply_standard,
            TranslationResult(word_sample=word_sample_hello),
        ),
        # A reply using non-standard key name
        (
            'Hello, world.',
            _reply_non_standard_key_name,
            TranslationResult(word_sample=word_sample_hello),
        ),
        # A reply which has extra content in the beginning and the end
        (
            'Hello, world.',
            _reply_with_extra_content,
            TranslationResult(word_sample=word_sample_hello),
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


_reply_words_standard = '''\

word: versions
normal_form: version
pronunciation: /ˈvərʒənz/
meaning: 版本

word: ambiguous
normal_form: ambiguous
pronunciation: /æmˈbɪɡjuəs/
meaning: 模棱两可的

word: nested
normal_form: nested
pronunciation: /ˈnɛstɪd/
meaning: 嵌套的'''

_reply_words_non_standard_key_name = '''\

Unknown-word: versions
normal_form: version
pronunciation: /ˈvərʒənz/
meaning: 版本'''


@pytest.mark.parametrize(
    'input,expected',
    [
        # A standard reply
        (
            _reply_words_standard,
            [
                WordChoice(
                    word='versions',
                    word_normal='version',
                    word_meaning='版本',
                    pronunciation='/ˈvərʒənz/',
                ),
                WordChoice(
                    word='ambiguous',
                    word_normal='ambiguous',
                    word_meaning='模棱两可的',
                    pronunciation='/æmˈbɪɡjuəs/',
                ),
                WordChoice(
                    word='nested',
                    word_normal='nested',
                    word_meaning='嵌套的',
                    pronunciation='/ˈnɛstɪd/',
                ),
            ],
        ),
        # A reply with non-standard key name
        (
            _reply_words_non_standard_key_name,
            [
                WordChoice(
                    word='versions',
                    word_normal='version',
                    word_meaning='版本',
                    pronunciation='/ˈvərʒənz/',
                ),
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
