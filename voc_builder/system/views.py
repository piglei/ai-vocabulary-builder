import logging

import cattrs
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

import voc_builder
from voc_builder.infras.store import get_sys_settings_store, get_word_store
from voc_builder.misc.version import get_new_version
from voc_builder.system.constants import (
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    OPENAI_MODELS,
    ModelProvider,
    TargetLanguage,
)
from voc_builder.system.language import get_target_language
from voc_builder.system.models import (
    AnthropicConfig,
    GeminiConfig,
    OpenAIConfig,
    build_default_settings,
)

from .serializers import (
    AnthropicConfigInput,
    GeminiConfigInput,
    OpenAIConfigInput,
    SettingsInput,
)

logger = logging.getLogger(__name__)

router = APIRouter()


MIN_WORDS_STORY = 6
MIN_WORDS_QUIZ = 5


@router.get("/api/system_status")
async def get_system_status(response: Response):
    """Get the system status."""
    settings = get_sys_settings_store().get_system_settings()
    model_settings_initialized = bool(settings and settings.model_provider)
    try:
        new_version = get_new_version()
    except Exception:
        logger.exception("Error checking new version.")
        new_version = None
    words_cnt = get_word_store().count()
    return JSONResponse(
        {
            "version": voc_builder.__version__,
            "target_language": get_target_language(),
            "model_settings_initialized": model_settings_initialized,
            "new_version": new_version,
            "words_cnt": words_cnt,
            "story_mode_available": words_cnt >= MIN_WORDS_STORY,
            "quiz_mode_available": words_cnt >= MIN_WORDS_QUIZ,
        }
    )


@router.get("/api/settings")
async def get_settings(response: Response):
    """Get the system settings."""
    settings = get_sys_settings_store().get_system_settings()
    if not settings:
        settings = build_default_settings()
    return JSONResponse(
        {
            "settings": cattrs.unstructure(settings),
            "model_options": {
                "gemini": GEMINI_MODELS,
                "openai": OPENAI_MODELS,
                "anthropic": ANTHROPIC_MODELS,
            },
            "target_language_options": [
                cattrs.unstructure(lan.value) for lan in TargetLanguage
            ],
        }
    )


@router.post("/api/settings")
async def save_settings(settings_input: SettingsInput, response: Response):
    """Save the system settings."""
    settings_store = get_sys_settings_store()
    settings = settings_store.get_system_settings()
    if not settings:
        settings = build_default_settings()

    settings.target_language = settings_input.target_language
    settings.model_provider = settings_input.model_provider
    # Update the model settings only for the selected provider type, validate the input
    # by pydantic models.
    if settings_input.model_provider == ModelProvider.OPENAI.value:
        o_obj = OpenAIConfigInput(**settings_input.openai_config)
        settings.openai_config = OpenAIConfig(**o_obj.model_dump(mode="json"))
    elif settings_input.model_provider == ModelProvider.GEMINI.value:
        g_obj = GeminiConfigInput(**settings_input.gemini_config)
        settings.gemini_config = GeminiConfig(**g_obj.model_dump(mode="json"))
    elif settings_input.model_provider == ModelProvider.ANTHROPIC.value:
        a_obj = AnthropicConfigInput(**settings_input.anthropic_config)
        settings.anthropic_config = AnthropicConfig(**a_obj.model_dump(mode="json"))

    settings_store.set_system_settings(settings)
    return {}
