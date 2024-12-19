import logging
from typing import List

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel

from voc_builder.exceptions import AIModelNotConfiguredError
from voc_builder.infras.store import get_sys_settings_store

logger = logging.getLogger(__name__)


class WordChoiceModelResp(BaseModel):
    """The word returned by LLM service."""

    word: str
    word_base_form: str
    definitions: str
    pronunciation: str

    def model_post_init(self, __context):
        # Always convert the word to lower case
        self.word = self.word.lower()

    def get_definition_list(self) -> List[str]:
        # The definitions are separated by "$"
        return [d.strip() for d in self.definitions.split("$")]


def create_ai_model():
    """Create the AI model object for calling with LLM service.

    :raise AIModelNotConfiguredError: when the model settings is invalid.
    """
    settings = get_sys_settings_store().get_system_settings()
    if not settings:
        raise AIModelNotConfiguredError("System settings not found")

    if settings.model_provider == "openai":
        openai_config = settings.openai_config
        client = AsyncOpenAI(
            api_key=openai_config.api_key, base_url=openai_config.api_host or None
        )
        return OpenAIModel(openai_config.model, openai_client=client)
    elif settings.model_provider == "gemini":
        gemini_config = settings.gemini_config
        if gemini_config.api_host:
            extra_kwargs = {
                "url_template": str(gemini_config.api_host).rstrip("/")
                + "/v1beta/models/{model}:"
            }
        else:
            extra_kwargs = {}
        return GeminiModel(
            gemini_config.model,  # type: ignore
            api_key=gemini_config.api_key,
            **extra_kwargs,  # type: ignore
        )
    elif settings.model_provider == "anthropic":
        anthropic_config = settings.anthropic_config
        assert anthropic_config
        a_client = AsyncAnthropic(
            api_key=anthropic_config.api_key, base_url=anthropic_config.api_host or None
        )
        return AnthropicModel(anthropic_config.model, anthropic_client=a_client)
    else:
        raise AIModelNotConfiguredError("Unknown model provider")
