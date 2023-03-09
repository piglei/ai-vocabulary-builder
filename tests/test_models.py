from voc_builder.models import WordChoice


class TestWordChoice:
    def test_extract_word(self):
        c = WordChoice('world', 'world', 'wɔrld', '世界')
        assert WordChoice.extract_word(c.get_console_display()) == 'world'
