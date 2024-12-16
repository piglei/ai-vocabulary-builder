from voc_builder.models import WordDefinition, WordSample


class Test__get_structured_definitions:
    def test_simple_value(self):
        w = WordSample(
            "detail",
            "detail",
            definitions=["细节"],
            pronunciation="ˈdiːteɪl",
            orig_text="",
            translated_text="",
        )
        assert w.get_structured_definitions() == [WordDefinition("", "细节")]

    def test_rich_value(self):
        w = WordSample(
            "detail",
            "detail",
            definitions=["[noun] 细节", "[noun] 详情", "[verb] 详述"],
            pronunciation="ˈdiːteɪl",
            orig_text="",
            translated_text="",
        )
        assert w.get_structured_definitions() == [
            WordDefinition("noun", "细节"),
            WordDefinition("noun", "详情"),
            WordDefinition("verb", "详述"),
        ]
