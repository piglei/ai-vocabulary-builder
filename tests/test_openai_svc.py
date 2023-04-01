import pytest

from voc_builder.models import WordChoice, WordSample
from voc_builder.openai_svc import parse_word_choices_reply

word_sample_hello = WordSample(
    word='world',
    word_normal='world',
    pronunciation='wɔːld',
    word_meaning='世界',
    orig_text='Hello, world.',
    translated_text='你好，世界。',
)

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


def test_parse_word_choices_reply_invalid_reply():
    _reply_words_missing_fields = '''\
word: versions
normal_form: version
'''
    with pytest.raises(ValueError):
        parse_word_choices_reply(_reply_words_missing_fields)
