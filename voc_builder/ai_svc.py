import logging
from typing import AsyncGenerator, List, Set

from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel

from voc_builder.exceptions import AIModelNotConfiguredError, AIServiceError
from voc_builder.models import WordChoice, WordSample
from voc_builder.store import get_sys_settings_store
from voc_builder.utils import get_word_candidates

logger = logging.getLogger()


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


async def get_translation(text: str) -> AsyncGenerator[str, None]:
    """Get the translated text of the given text.

    :param text: The text which needs to be translated.
    :return: The translation text.
    :raise AIServiceError: when unable to finish the API call or reply is malformed.
    """

    try:
        async for translated_text in query_translation(text):
            yield translated_text
    except Exception as e:
        raise AIServiceError("Error calling AI backend API: %s" % e)


# The prompt being used to translate text
prompt_main_system = """\
You are a translation assistant, I will give you a paragraph of english, please \
translate it into simplified Chinese, the answer should only include the translated \
content and have no extra content.
"""

prompt_main_user_tmpl = """\
The paragraph is:

{text}
"""


async def query_translation(text: str) -> AsyncGenerator[str, None]:
    """Query the AI to get the translation."""
    user_content = prompt_main_user_tmpl.format(text=text)
    prompt = prompt_main_system + "\n" + user_content
    agent: Agent = Agent(create_ai_model())

    async with agent.run_stream(prompt) as result:
        async for message in result.stream():
            yield message


# The prompt being used to extract multiple words
prompt_rare_word_system = """You are a english reading specialist, I will give you a list \
of english words separated by ",", please find the most rarely encountered word as the result. \

Reply the result word, the base form, the simplified Chinese definition and \
the pronunciation of the result word.

- List all possible definitions, separated by "$", with each formatted as \
"[{{part of speech(adj/noun/...)}}] {{simplified Chinese definition}}".
    - Example: [noun] 熊 $ [verb] 忍受
- A paragraph will be given as a reference because there might be homographs.
"""  # noqa: E501


prompt_rare_word_user_tmpl = """\
Words: {words}

Paragraph for reference: {text}
"""


async def get_rare_word(text: str, known_words: Set[str]) -> WordChoice:
    """Get the most rarely word in given text."""
    words = get_word_candidates(text, known_words=known_words)
    if not words:
        raise AIServiceError("Text does not contain any words that meet the criteria")

    user_content = prompt_rare_word_user_tmpl.format(text=text, words=",".join(words))
    prompt = prompt_rare_word_system + user_content
    agent: Agent = Agent(create_ai_model(), result_type=WordChoiceModelResp)
    try:
        result = await agent.run(prompt)
    except Exception as e:
        raise AIServiceError("Error calling AI backend API: %s" % e)

    item = result.data
    return WordChoice(
        word=item.word,
        word_normal=item.word_base_form,
        pronunciation=item.pronunciation,
        definitions=item.get_definition_list(),
    )


prompt_word_manually_system = """You are a translation assistant, I will give you a \
a english word.

Reply the word, the base form, the simplified Chinese definition and the \
pronunciation of the word.

- List all possible definitions, separated by "$", with each formatted as \
"[{{part of speech(adj/noun/...)}}] {{simplified Chinese definition}}".
    - Example: [noun] 熊 $ [verb] 忍受
- A paragraph will be given as a reference because there might be homographs.
"""  # noqa: E501


prompt_word_manually_user_tmpl = """\
Word: {word}

Paragraph for reference: {text}
"""


async def get_word_manually(text: str, word: str) -> WordChoice:
    """Get a word that is manually selected by user.

    :param text: The text which contains the word.
    :param word: The selected word.
    :raise: AIServiceError
    """
    user_content = prompt_word_manually_user_tmpl.format(text=text, word=word)
    prompt = prompt_word_manually_system + user_content
    agent: Agent = Agent(create_ai_model(), result_type=WordChoiceModelResp)
    try:
        result = await agent.run(prompt)
    except Exception as e:
        raise AIServiceError("Error calling AI backend API: %s" % e)

    item = result.data
    return WordChoice(
        word=item.word,
        word_normal=item.word_base_form,
        pronunciation=item.pronunciation,
        definitions=item.get_definition_list(),
    )


async def get_story(words: List[WordSample]) -> AsyncGenerator[str, None]:
    """Query AI backend API to get a story.

    :param live_info: The info object which represents the writing procedure
    :return: The story text
    :raise: AIServiceError
    """
    # Try to use the normal form of each word
    str_words = [w.word_normal or w.word for w in words]
    try:
        async for message in query_story(str_words):
            yield message
    except Exception as e:
        raise AIServiceError("Error querying OpenAI API: %s" % e)


# The prompt being used to generate stroy from words
prompt_write_story_user_tmpl = """\
Please write a short story which is less than {total_words_cnt} words, the story should use simple \
words and these special words must be included: {words}.  Also surround every special word \
with a single "$" character at the beginning and the end."""  # noqa: E501


async def query_story(words: List[str]) -> AsyncGenerator[str, None]:
    """Query AI backend API to get a story.

    :param stream_handler: A callback function to handle partial replies.
    :return: The story text
    """
    words_str = ",".join(words)
    prompt = prompt_write_story_user_tmpl.format(
        words=words_str, total_words_cnt=len(words) * 30
    )
    agent: Agent = Agent(create_ai_model())
    async with agent.run_stream(prompt) as result:
        async for message in result.stream():
            yield message


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
    else:
        raise AIModelNotConfiguredError("Unknown model provider")
