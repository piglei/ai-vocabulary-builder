from voc_builder.commands.remove import handle_remove
from voc_builder.store import get_mastered_word_store, get_word_store


class TestHandleRemove:
    def test_normal(self, w_sample_world):
        get_word_store().add(w_sample_world)
        # Add an invalid word
        handle_remove(["world", "invalid-word"], hard_remove=False)
        assert get_word_store().exists(w_sample_world.word) is False
        assert get_mastered_word_store().exists(w_sample_world.word) is True
        assert get_mastered_word_store().exists("invalid-word") is False

    def test_hard_remove(self, w_sample_world):
        get_word_store().add(w_sample_world)
        handle_remove(["world", "invalid-word"], hard_remove=True)
        assert get_word_store().exists(w_sample_world.word) is False
        assert get_mastered_word_store().exists(w_sample_world.word) is False
