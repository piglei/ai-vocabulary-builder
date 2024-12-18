import datetime
import json
from io import StringIO
from typing import AsyncGenerator, Dict, List, Literal

from fastapi import APIRouter, Query, Response, status
from sse_starlette.sse import EventSourceResponse
from starlette.responses import StreamingResponse
from typing_extensions import Annotated

from voc_builder.builder.models import WordSample
from voc_builder.builder.serializers import WordSampleOutput
from voc_builder.exceptions import AIServiceError
from voc_builder.infras.ai import create_ai_model
from voc_builder.infras.store import get_mastered_word_store, get_word_store
from voc_builder.misc.export import VocCSVWriter

from .ai_svc import get_story
from .serializers import DeleteMasteredWordsInput

router = APIRouter()


@router.get("/api/quiz/words/")
def get_words_for_quiz(words_num: Annotated[Literal["5", "10", "25", "50"], Query(...)]):
    """Get words for generating the quiz."""
    word_store = get_word_store()
    words = word_store.pick_quiz_words(int(words_num))
    word_store.update_quiz_words(words)
    return [WordSampleOutput.from_db_obj(w) for w in words]


@router.get("/api/stories/")
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
        async for text in get_story(create_ai_model(), words):
            yield {"event": "story_partial", "data": text}
    except AIServiceError as e:
        yield {"event": "error", "data": json.dumps({"message": str(e)})}
    yield {"event": "story", "data": text}


@router.get("/api/word_samples/export/")
def export_words():
    """Export all the word samples."""
    fp = StringIO()
    VocCSVWriter().write_to(fp)
    fp.seek(0)

    now = datetime.datetime.now()
    filename = now.strftime("ai_vov_words_%Y%m%d_%H%M.csv")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(fp, headers=headers)


@router.get("/api/mastered_words/")
def get_mastered_words():
    """Get all mastered words."""
    words = get_mastered_word_store().all()
    return {"words": words, "count": len(words)}


@router.post("/api/mastered_words/deletion/")
def delete_mastered_words(req: DeleteMasteredWordsInput, response: Response):
    """Delete words from the mastered words."""
    mastered_word_s = get_mastered_word_store()
    for word in req.words:
        mastered_word_s.remove(word)
    response.status_code = status.HTTP_204_NO_CONTENT
