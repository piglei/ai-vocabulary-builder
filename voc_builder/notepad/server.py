import datetime
import json
import logging
import pathlib
from io import StringIO
from typing import AsyncGenerator, Dict, List, Literal

import cattrs
from fastapi import FastAPI, Query, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sse_starlette.sse import EventSourceResponse
from starlette.responses import FileResponse, StreamingResponse
from typing_extensions import Annotated

import voc_builder
from voc_builder.ai_svc import (
    get_rare_word,
    get_story,
    get_translation,
    get_word_manually,
)
from voc_builder.constants import GEMINI_MODELS, OPENAI_MODELS, ModelProvider
from voc_builder.exceptions import AIServiceError
from voc_builder.export import VocCSVWriter
from voc_builder.models import (
    GeminiConfig,
    OpenAIConfig,
    WordSample,
    build_default_settings,
)
from voc_builder.store import (
    get_mastered_word_store,
    get_sys_settings_store,
    get_word_store,
)
from voc_builder.utils import tokenize_text
from voc_builder.version import get_new_version

from .errors import (
    api_error_exception_handler,
    error_codes,
    pydantic_exception_handler,
    req_validation_exception_handler,
)
from .serializers import (
    DeleteMasteredWordsInput,
    DeleteWordsInput,
    GeminiConfigInput,
    GetKnownWordsByTextInput,
    ManuallySelectInput,
    OpenAIConfigInput,
    SettingsInput,
    TranslatedTextInput,
    WordSampleOutput,
)
from .std_err import APIError

logger = logging.getLogger(__name__)

ROOT_DIR = pathlib.Path(__file__).parent.resolve()

app = FastAPI()

app.add_exception_handler(ValidationError, pydantic_exception_handler)  # type: ignore
app.add_exception_handler(RequestValidationError, req_validation_exception_handler)  # type: ignore
app.add_exception_handler(APIError, api_error_exception_handler)  # type: ignore
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
@app.get("/app/{any_path:path}")
def index():
    return FileResponse(str(ROOT_DIR / "dist/index.html"))


@app.get("/api/translations/")
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
        async for translated_text in get_translation(text):
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


@app.post("/api/word_samples/extractions/")
async def create_word_sample(trans_obj: TranslatedTextInput, response: Response):
    """Create a new word sample from the translated result."""
    mastered_word_s = get_mastered_word_store()
    word_store = get_word_store()

    orig_words = tokenize_text(trans_obj.orig_text)
    # Words already in vocabulary book and marked as mastered are treated as "known"
    known_words = word_store.filter(orig_words) | mastered_word_s.filter(orig_words)

    try:
        choice = await get_rare_word(trans_obj.orig_text, known_words)
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


@app.post("/api/known_words/find_by_text/")
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


@app.post("/api/word_samples/deletion/")
def delete_word_samples(req: DeleteWordsInput, response: Response):
    """Delete a list of words."""
    word_store = get_word_store()
    mastered_word_s = get_mastered_word_store()
    for word in req.words:
        word_store.remove(word)
        if req.mark_mastered:
            mastered_word_s.add(word)
    response.status_code = status.HTTP_204_NO_CONTENT


@app.get("/api/word_samples/")
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


@app.post("/api/word_samples/manually_save/")
async def manually_save(req: ManuallySelectInput, response: Response):
    """Manually save a word to the store."""
    word_store = get_word_store()

    try:
        choice = await get_word_manually(req.orig_text, req.word)
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


@app.get("/api/system_status")
async def get_system_status(response: Response):
    """Get the system status."""
    settings = get_sys_settings_store().get_system_settings()
    model_settings_initialized = bool(settings and settings.model_provider)
    try:
        new_version = get_new_version()
    except Exception:
        logger.exception("Error checking new version.")
        new_version = None
    return JSONResponse(
        {
            "version": voc_builder.__version__,
            "model_settings_initialized": model_settings_initialized,
            "new_version": new_version,
        }
    )


@app.get("/api/settings")
async def get_settings(response: Response):
    """Get the system settings."""
    settings = get_sys_settings_store().get_system_settings()
    if not settings:
        settings = build_default_settings()
    return JSONResponse(
        {
            "settings": cattrs.unstructure(settings),
            "model_options": {"gemini": GEMINI_MODELS, "openai": OPENAI_MODELS},
        }
    )


@app.post("/api/settings")
async def save_settings(settings_input: SettingsInput, response: Response):
    """Save the system settings."""
    settings_store = get_sys_settings_store()
    settings = settings_store.get_system_settings()
    if not settings:
        settings = build_default_settings()

    settings.model_provider = settings_input.model_provider
    # Update the model settings only for the selected provider type, validate the input
    # by pydantic models.
    if settings_input.model_provider == ModelProvider.OPENAI.value:
        o_obj = OpenAIConfigInput(**settings_input.openai_config)
        settings.openai_config = OpenAIConfig(**o_obj.model_dump(mode="json"))
    elif settings_input.model_provider == ModelProvider.GEMINI.value:
        g_obj = GeminiConfigInput(**settings_input.gemini_config)
        settings.gemini_config = GeminiConfig(**g_obj.model_dump(mode="json"))

    settings_store.set_system_settings(settings)
    return {}


@app.get("/api/stories/")
def create_new_story(words_num: Annotated[Literal["6", "12", "24"], Query(...)]):
    """Create a new story."""
    word_store = get_word_store()
    words = word_store.pick_story_words(int(words_num))
    word_store.update_story_words(words)
    return EventSourceResponse(gen_story_sse(words))


async def gen_story_sse(words: List[WordSample]) -> AsyncGenerator[Dict, None]:
    """Generate the SSE events for the story writing progress."""
    out_words = [WordSampleOutput.from_db_obj(w) for w in words]
    yield {
        "event": "words",
        "data": json.dumps([w.model_dump(mode="json") for w in out_words]),
    }

    try:
        async for text in get_story(words):
            yield {"event": "story_partial", "data": text}
    except AIServiceError as e:
        yield {"event": "error", "data": json.dumps({"message": str(e)})}
    yield {"event": "story", "data": text}


@app.get("/api/mastered_words/")
def get_mastered_words():
    """Get all mastered words."""
    words = get_mastered_word_store().all()
    return {"words": words, "count": len(words)}


@app.post("/api/mastered_words/deletion/")
def delete_mastered_words(req: DeleteMasteredWordsInput, response: Response):
    """Delete words from the mastered words."""
    mastered_word_s = get_mastered_word_store()
    for word in req.words:
        mastered_word_s.remove(word)
    response.status_code = status.HTTP_204_NO_CONTENT


@app.get("/api/word_samples/export/")
def export_words():
    """Export all the word samples."""
    fp = StringIO()
    VocCSVWriter().write_to(fp)
    fp.seek(0)

    now = datetime.datetime.now()
    filename = now.strftime("ai_vov_words_%Y%m%d_%H%M.csv")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(fp, headers=headers)


def validate_result_word(word: WordSample, orig_text: str):
    """Check if a result word is valid before it can be put into vocabulary book"""
    if get_word_store().exists(word.word):
        raise error_codes.WORD_ALREADY_EXISTS.set_data(word.word)
