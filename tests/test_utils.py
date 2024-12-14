from voc_builder.utils import highlight_story_text, highlight_words, tokenize_text


def test_tokenize_text():
    s = "Welcome! This is the official documentation for Python 3.11.2."
    assert tokenize_text(s) == {
        "documentation",
        "the",
        "is",
        "welcome",
        "this",
        "python",
        "official",
        "for",
    }


def test_highlight_words():
    s = "Welcome! This is the official documentation for Python."
    assert (
        highlight_words(s, ["welcome", "python"])
        == "[bold][underline]Welcome[/underline][/bold]! This is the official documentation for [bold][underline]Python[/underline][/bold]."  # noqa: E501
    )


def test_highlight_words_with_extra_style():
    s = "Welcome! This is the official documentation for Python."
    assert (
        highlight_words(s, ["welcome", "python"], extra_style="red")
        == "[bold][underline][red]Welcome[/red][/underline][/bold]! This is the official documentation for [bold][underline][red]Python[/red][/underline][/bold]."  # noqa: E501
    )


def test_highlight_story_text():
    s = "Jennifer believed that the ${serendipitous}$ meeting"
    assert (
        highlight_story_text(s)
        == "Jennifer believed that the [bold][underline]serendipitous[/underline][/bold] meeting"
    )
