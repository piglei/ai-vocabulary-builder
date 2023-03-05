from voc_builder.utils import tokenize_text


def test_tokenize_text():
    s = 'Welcome! This is the official documentation for Python 3.11.2.'
    assert tokenize_text(s) == {
        'documentation',
        'the',
        'is',
        'welcome',
        'this',
        'python',
        'official',
        'for',
    }
