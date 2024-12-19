import json
import logging
from typing import AsyncGenerator, Dict

from fastapi import APIRouter, Query, Response, status
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from typing_extensions import Annotated

from voc_builder.builder.models import WordSample
from voc_builder.common.errors import error_codes
from voc_builder.common.text import tokenize_text
from voc_builder.exceptions import AIServiceError
from voc_builder.infras.ai import create_ai_model
from voc_builder.infras.store import get_mastered_word_store, get_word_store
from voc_builder.system.language import get_target_language

from .ai_svc import get_rare_word, get_translation, get_word_manually
from .serializers import (
    DeleteWordsInput,
    GetKnownWordsByTextInput,
    ManuallySelectInput,
    TranslatedTextInput,
    WordSampleOutput,
)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/api/translations/")
def create_new_translations(
    user_text: Annotated[str, Query(min_length=12, max_length=1600)],
):
    """Create a new translation, return the response in SSE protocol."""
    return EventSourceResponse(gen_translation_sse(user_text))


async def gen_translation_sse(text: str) -> AsyncGenerator[Dict, None]:
    """Generate the SSE events for the translation progress.

    :param text: The text to be translated.
    """
    try:
        async for translated_text in get_translation(
            create_ai_model(), text, get_target_language()
        ):
            yield {
                "event": "trans_partial",
                "data": json.dumps({"translated_text": translated_text}),
            }
    except AIServiceError as e:
        yield {"event": "error", "data": json.dumps({"message": str(e)})}
        return

    yield {
        "event": "translation",
        "data": json.dumps({"text": text, "translated_text": translated_text}),
    }


@router.post("/api/word_samples/extractions/")
async def create_word_sample(trans_obj: TranslatedTextInput, response: Response):
    """Create a new word sample from the translated result."""
    mastered_word_s = get_mastered_word_store()
    word_store = get_word_store()

    orig_words = tokenize_text(trans_obj.orig_text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = word_store.filter(orig_words) | mastered_word_s.filter(orig_words)

    try:
        choice = await get_rare_word(
            create_ai_model(), trans_obj.orig_text, known_words, get_target_language()
        )
    except Exception as exc:
        logger.exception("Error extracting word.")
        raise error_codes.EXACTING_WORD_FAILED.format(str(exc))

    word_sample = WordSample(
        word=choice.word,
        word_normal=choice.word_normal,
        definitions=choice.definitions,
        pronunciation=choice.pronunciation,
        translated_text=trans_obj.translated_text,
        orig_text=trans_obj.orig_text,
    )

    validate_result_word(word_sample, trans_obj.orig_text)

    word_store.add(word_sample)
    return {
        "word_sample": WordSampleOutput.from_db_obj(word_sample),
        "count": word_store.count(),
    }


@router.post("/api/known_words/find_by_text/")
def find_known_words_by_text(req: GetKnownWordsByTextInput, response: Response):
    """Find all known words in the vocabulary book by the given text."""
    mastered_word_s = get_mastered_word_store()
    word_store = get_word_store()

    orig_words = tokenize_text(req.text)

    # Words already in vocabulary book and marked as mastered are treated as "known"
    existing_words = []
    for w in word_store.filter(orig_words):
        word_obj = word_store.get(w)
        assert word_obj
        obj = WordSampleOutput.from_db_obj(word_obj.ws)
        existing_words.append(
            {"word": obj.word, "simple_definition": obj.simple_definition}
        )

    mastered_words = mastered_word_s.filter(orig_words)
    return JSONResponse(
        {"existing_words": list(existing_words), "mastered_words": list(mastered_words)}
    )


@router.post("/api/word_samples/deletion/")
def delete_word_samples(req: DeleteWordsInput, response: Response):
    """Delete a list of words."""
    word_store = get_word_store()
    mastered_word_s = get_mastered_word_store()
    for word in req.words:
        word_store.remove(word)
        if req.mark_mastered:
            mastered_word_s.add(word)
    response.status_code = status.HTTP_204_NO_CONTENT


@router.get("/api/word_samples/")
def list_word_samples():
    """List all word samples in the store."""
    word_store = get_word_store()
    words = word_store.list_latest()
    # Remove the fields not necessary, sort by -date_added
    words_refined = [
        {"ws": WordSampleOutput.from_db_obj(obj.ws), "ts_date_added": obj.ts_date_added}
        for obj in reversed(words)
    ]
    return {"words": words_refined, "count": len(words)}


@router.get("/api/word_samples/recent")
def list_recent_word_samples():
    """List the most recent word samples in the store."""
    word_store = get_word_store()
    words = word_store.list_latest(limit=4)
    # Remove the fields not necessary, sort by -date_added
    words_refined = [WordSampleOutput.from_db_obj(obj.ws) for obj in reversed(words)]
    return {"words": words_refined, "count": len(words)}


@router.post("/api/word_samples/manually_save/")
async def manually_save(req: ManuallySelectInput, response: Response):
    """Manually save a word to the store."""
    word_store = get_word_store()

    try:
        choice = await get_word_manually(
            create_ai_model(), req.orig_text, req.word, get_target_language()
        )
    except Exception as exc:
        raise error_codes.MANUALLY_SAVE_WORD_FAILED.format(str(exc))

    word_sample = WordSample(
        word=choice.word,
        word_normal=choice.word_normal,
        definitions=choice.definitions,
        pronunciation=choice.pronunciation,
        translated_text=req.translated_text,
        orig_text=req.orig_text,
    )

    validate_result_word(word_sample, req.orig_text)

    word_store.add(word_sample)
    return {
        "word_sample": WordSampleOutput.from_db_obj(word_sample),
        "count": word_store.count(),
    }


def validate_result_word(word: WordSample, orig_text: str):
    """Check if a result word is valid before it can be put into vocabulary book"""
    if get_word_store().exists(word.word):
        raise error_codes.WORD_ALREADY_EXISTS.set_data(word.word)
