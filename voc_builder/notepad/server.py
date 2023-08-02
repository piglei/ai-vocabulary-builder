import pathlib
import asyncio
import json
import logging
from dataclasses import asdict
from typing import AsyncGenerator, Dict, List

from fastapi import FastAPI, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, conlist
from sse_starlette.sse import EventSourceResponse
from starlette.responses import FileResponse
from typing_extensions import Annotated

from voc_builder.exceptions import OpenAIServiceError, WordInvalidForAdding
from voc_builder.models import LiveTranslationInfo, WordSample
from voc_builder.openai_svc import get_translation, get_uncommon_word, get_word_choices
from voc_builder.store import get_mastered_word_store, get_word_store
from voc_builder.utils import tokenize_text

logger = logging.getLogger(__name__)

ROOT_DIR = pathlib.Path(__file__).parent.resolve()

app = FastAPI()

app.mount("/assets", StaticFiles(directory=str(ROOT_DIR / "dist/assets")), name="assets")


# TODO: Should we restrict the allowed origins?
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/manage")
def index():
    return FileResponse(str(ROOT_DIR / 'dist/index.html'))


@app.get("/api/translations/")
def create_new_translations(user_text: Annotated[str, Query(min_length=12, max_length=1600)]):
    """Create a new translation, return the response in SSE protocol."""
    return EventSourceResponse(gen_translation_sse(user_text))


async def gen_translation_sse(text: str) -> AsyncGenerator[Dict, None]:
    """Generate the SSE events for the translation progress.

    :param text: The text to be translated.
    """
    live_info = LiveTranslationInfo()
    # Start the translation task in background
    loop = asyncio.get_running_loop()
    task_trans = loop.run_in_executor(None, get_translation, text, live_info)

    # Send the partial translation to the client
    sent_length = 0
    while not live_info.is_finished and not task_trans.done():
        if len(live_info.translated_text) > sent_length:
            yield {
                "event": "trans_partial",
                "data": json.dumps({"text": live_info.translated_text[sent_length:]}),
            }
            sent_length = len(live_info.translated_text)
        await asyncio.sleep(0.1)

    # Send the full translation to the client
    try:
        await task_trans
    except Exception as exc:
        logger.exception("Error getting translation.")
        yield {"event": "error", "data": json.dumps({'message': str(exc)})}
        return

    yield {"event": "translation", "data": json.dumps(asdict(task_trans.result()))}


class TranslatedText(BaseModel):
    """A text with its translation

    :param orig_text: The original text
    :param translated_text: The translated text
    """

    orig_text: str
    translated_text: str


@app.post("/api/word_samples/extractions/")
def create_word_sample(trans_obj: TranslatedText, response: Response):
    """Create a new word sample from the translated result."""
    mastered_word_s = get_mastered_word_store()
    word_store = get_word_store()

    orig_words = tokenize_text(trans_obj.orig_text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = word_store.filter(orig_words) | mastered_word_s.filter(orig_words)

    try:
        choice = get_uncommon_word(trans_obj.orig_text, known_words)
    except Exception as exc:
        logger.exception("Error extracting word.")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "service_error", "message": str(exc)}

    word_sample = WordSample(
        word=choice.word,
        word_normal=choice.word_normal,
        word_meaning=choice.word_meaning,
        pronunciation=choice.pronunciation,
        translated_text=trans_obj.translated_text,
        orig_text=trans_obj.orig_text,
    )

    try:
        validate_result_word(word_sample, trans_obj.orig_text)
    except WordInvalidForAdding as e:
        logger.exception(f'Unable to add "{word_sample.word}", reason: {e}')
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "word_invalid", "message": f"the word is invalid: {e}"}

    word_store.add(word_sample)
    return {"word_sample": word_sample, "count": word_store.count()}


@app.post("/api/word_samples/deletion/")
def delete_word_samples(words: List[str], response: Response):
    """Delete a list of words."""
    for word in words:
        get_word_store().remove(word)
    response.status_code = status.HTTP_204_NO_CONTENT


@app.post("/api/word_choices/extractions/")
def extract_word_choices(trans_obj: TranslatedText, response: Response):
    """Extract a new word from a translated text automatically."""
    mastered_word_s = get_mastered_word_store()
    word_store = get_word_store()

    orig_words = tokenize_text(trans_obj.orig_text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = word_store.filter(orig_words) | mastered_word_s.filter(orig_words)

    try:
        choices = get_word_choices(trans_obj.orig_text, known_words)
    except OpenAIServiceError as exc:
        logger.exception("Error extracting choices.")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "service_error", "message": str(exc)}

    return {"word_choices": choices}


class WordChoice(BaseModel):
    word: str
    word_normal: str
    word_meaning: str
    pronunciation: str


class WordChoicesForSave(BaseModel):
    """Accept a list of choices for saving"""

    orig_text: str = Field(..., min_length=1)
    translated_text: str = Field(..., min_length=1)
    choices: conlist(WordChoice, min_items=1)


@app.post("/api/word_choices/save/")
def save_word_choices(user_choices: WordChoicesForSave, response: Response):
    """Save a list of word choices to the store."""
    word_store = get_word_store()

    words: List[WordSample] = []
    failed_words: List[WordSample] = []
    for word_sample in user_choices.choices:
        sample = WordSample(
            word=word_sample.word,
            word_normal=word_sample.word_normal,
            word_meaning=word_sample.word_meaning,
            pronunciation=word_sample.pronunciation,
            translated_text=user_choices.translated_text,
            orig_text=user_choices.orig_text,
        )
        try:
            validate_result_word(sample, sample.orig_text)
        except WordInvalidForAdding as e:
            logger.exception(f'Unable to add "{word_sample.word}", reason: {e}')
            failed_words.append(sample)
        else:
            words.append(sample)

    if not words:
        return {"error": "choices_invalid", "message": "all choices are invalid for adding"}

    word_store = get_word_store()
    for word in words:
        word_store.add(word)

    return {"added_words": words, "failed_words": failed_words, "count": word_store.count()}


@app.get("/api/word_samples/")
def list_word_samples():
    """List all word samples in the store."""
    word_store = get_word_store()
    words = word_store.list_latest()
    # Remove the fields not necessary, sort by -date_added
    words_refined = [{"ws": obj.ws, "ts_date_added": obj.ts_date_added} for obj in reversed(words)]
    return {"words": words_refined, "count": len(words)}


def validate_result_word(word: WordSample, orig_text: str):
    """Check if a result word is valid before it can be put into vocabulary book"""
    if get_word_store().exists(word.word):
        raise WordInvalidForAdding('already in your vocabulary book')
    if get_mastered_word_store().exists(word.word):
        raise WordInvalidForAdding('already mastered')
    if word.word not in orig_text.lower():
        raise WordInvalidForAdding('not in the original text')
