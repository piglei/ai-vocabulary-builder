from voc_builder.store import MasteredWordStore


class TestMasteredWordsStore:
    def test_filter(self, tmp_path):
        mastered_words_s = MasteredWordStore(tmp_path / 'foo.json')
        mastered_words_s.add('program')
        mastered_words_s.add('python')
        assert mastered_words_s.filter({'foo', 'python', 'bar'}) == {'python'}

    def test_repeated_add(self, tmp_path):
        mastered_words_s = MasteredWordStore(tmp_path / 'foo.json')
        mastered_words_s.add('program')
        mastered_words_s.add('program')
        mastered_words_s.add('python')
        assert set(mastered_words_s.all()) == {'python', 'program'}

    def test_exists(self, tmp_path):
        mastered_words_s = MasteredWordStore(tmp_path / 'foo.json')
        assert mastered_words_s.exists('program') is False
        mastered_words_s.add('program')
        assert mastered_words_s.exists('program') is True

    def test_remove(self, tmp_path):
        mastered_words_s = MasteredWordStore(tmp_path / 'foo.json')
        mastered_words_s.add('program')
        assert mastered_words_s.exists('program') is True
        mastered_words_s.remove('program')
        assert mastered_words_s.exists('program') is False
