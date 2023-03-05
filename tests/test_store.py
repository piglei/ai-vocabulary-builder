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
