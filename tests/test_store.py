from voc_builder.models import WordSample
from voc_builder.store import MasteredWordStore, WordStore


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


class TestWordStore:
    def test_get(self, tmp_path):
        word_store = WordStore(tmp_path / 'foo.json')
        word_store.add(WordSample.make_empty('program'))
        obj = word_store.get('program')
        assert obj and obj.word == 'program'

    def test_misc(self, tmp_path):
        word_store = WordStore(tmp_path / 'foo.json')
        word_store.add(WordSample.make_empty('program'))
        word_store.add(WordSample.make_empty('program'))
        word_store.add(WordSample.make_empty('python'))
        assert word_store.count() == 2
        assert list(word_store.all())[0].word == 'program'

        word_store.remove('program')
        assert word_store.count() == 1

    def test_story_words(self, tmp_path):
        word_store = WordStore(tmp_path / 'foo.json')
        for s in 'Python program language is easy to read and write'.split():
            word_store.add(WordSample.make_empty(s))

        words = word_store.pick_story_words(count=1)
        assert len(words) == 1
        word_store.update_story_words(words)
        first_word = words[0]

        # Check the status was updated
        obj = word_store.get(first_word.word)
        assert obj and obj.wp.storied_cnt == 1 and obj.wp.ts_date_storied is not None

        # Now the `pick_story_words` call should return a different word
        new_words = word_store.pick_story_words(count=1)
        assert new_words[0] != first_word
