from unittest import mock

from voc_builder.builder import VocBuilderCSVFile
from voc_builder.models import WordSample


class TestVocBuilderCSVFile:
    def test_is_duplicated(self, tmp_path, w_sample_world):
        builder = VocBuilderCSVFile(tmp_path / 'foo.csv')
        assert builder.is_duplicated(w_sample_world) is False

        builder.append_word(w_sample_world)
        assert builder.is_duplicated(w_sample_world) is True

    def test_find_known_words(self, tmp_path, w_sample_world):
        builder = VocBuilderCSVFile(tmp_path / 'foo.csv')
        builder.append_word(w_sample_world)
        assert builder.find_known_words({'hello', 'world'}) == {'world'}

    def test_repeated_calls(self, tmp_path, w_sample_world):
        p = tmp_path / 'foo.csv'
        builder = VocBuilderCSVFile(p)
        builder.append_word(w_sample_world)

        words = builder.read_all()
        assert len(words) == 1
        assert words[0].word == 'world'
        assert words[0].word_meaning == '世界'
        assert words[0].translated_text == '你好，世界！'

        # re-initialize the obj and append another word
        builder_2 = VocBuilderCSVFile(p)
        builder_2.append_word(WordSample('hello', '你好', 'həˈlō', 'Hello.', '你好。'))

        words_2 = builder_2.read_all()
        assert len(words_2) == 2
        assert words_2[1].word == 'hello'
        assert words_2[1].word_meaning == '你好'
        assert words_2[1].translated_text == '你好。'

    def test_remove_word(self, tmp_path, w_sample_world):
        builder = VocBuilderCSVFile(tmp_path / 'foo.csv')
        with mock.patch.object(builder, 'get_current_date', return_value='special_date'):
            builder.append_word(w_sample_world)
            builder.append_word(WordSample('hello', '你好', 'həˈlō', 'Hello.', '你好。'))
            words = list(builder.read_all_with_meta())
            assert len(words) == 2
            assert words[0][1] == 'special_date'

        builder.remove_words({'world'})
        words = list(builder.read_all_with_meta())
        assert len(words) == 1
        assert words[0][0].word == 'hello'
        # The date_added should remain intact
        assert words[0][1] == 'special_date'
