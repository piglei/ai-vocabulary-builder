import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, List

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel

from voc_builder.exceptions import AIModelNotConfiguredError
from voc_builder.infras.store import get_sys_settings_store
from voc_builder.system.models import SystemSettings

logger = logging.getLogger(__name__)


@dataclass
class PromptText:
    """A simple prompt type helps configuring AI prompt.

    :param system: The system prompts.
    :param user: The user prompts.
    """

    system_lines: List[str]
    user_lines: List[str]

    @property
    def system(self) -> str:
        return "\n\n".join(self.system_lines)

    @property
    def user(self) -> str:
        return "\n\n".join(self.user_lines)


class AIResultMode(str, Enum):
    """The mode to get the AI result."""

    PYDANTIC = "pydantic"
    # JSON mode is for some OpenAI compatible API that doesn't support function call
    JSON = "json"


@dataclass
class AIModelConfig:
    """The AI model configuration, it controls how to interact with the AI model.

    :param model: The AI model object.
    :param result_mode: The result mode to get the AI result.
    """

    model: Any
    result_mode: AIResultMode


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


def create_ai_model_config() -> AIModelConfig:
    """Create the AI model configuration."""
    settings = get_sys_settings_store().get_system_settings()
    if not settings:
        raise AIModelNotConfiguredError("System settings not found")

    model = create_ai_model(settings)
    if settings.model_provider == "deepseek":
        result_mode = AIResultMode.JSON
    else:
        result_mode = AIResultMode.PYDANTIC
    return AIModelConfig(model, result_mode)


# The default base URL for Deepseek API
DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"


def create_ai_model(settings: SystemSettings):
    """Create the AI model object for calling with LLM service.

    :raise AIModelNotConfiguredError: when the model settings is invalid.
    """
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
    elif settings.model_provider == "deepseek":
        deepseek_config = settings.deepseek_config
        assert deepseek_config
        client = AsyncOpenAI(
            api_key=deepseek_config.api_key,
            base_url=deepseek_config.api_host or DEEPSEEK_DEFAULT_BASE_URL,
        )
        return OpenAIModel(deepseek_config.model, openai_client=client)
    else:
        raise AIModelNotConfiguredError("Unknown model provider")
