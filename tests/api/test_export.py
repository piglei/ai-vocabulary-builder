import datetime
import zipfile
from io import BytesIO

from voc_builder.builder.models import WordSample
from voc_builder.infras.store import get_word_store


class TestExportWordsToAnki:
    path_export_anki = "/api/word_samples/export/anki/"

    def test_export_anki_by_time(self, client, w_sample_world):
        _add_word(
            word_sample=w_sample_world,
            ts=datetime.datetime(2024, 1, 1, 12, 0),
        )

        _add_word(
            word_sample=WordSample(
                word="python",
                word_normal="python",
                definitions=["Python 编程语言"],
                pronunciation="ˈpaɪθɒn",
                orig_text="Python is a programming language.",
                translated_text="Python 是一种编程语言。",
            ),
            ts=datetime.datetime(2023, 12, 30, 8, 0),
        )

        resp = client.post(
            self.path_export_anki,
            json={"start_date": "2024-01-01", "end_date": "2024-01-02"},
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/apkg"
        assert zipfile.is_zipfile(BytesIO(resp.content))

    def test_export_words_to_anki_rejects_invalid_range(self, client):
        resp = client.post(
            self.path_export_anki,
            json={
                "start_date": "2024-02-01",
                "end_date": "2024-01-01",
            },
        )

        assert resp.status_code == 400
        assert (
            resp.json()["message"]
            == "Validation error: End date must be after start date"
        )


def _add_word(word_sample: WordSample, ts: datetime.datetime) -> None:
    """Helper to add word sample with a fixed timestamp."""
    get_word_store().add(word_sample, ts.timestamp())
