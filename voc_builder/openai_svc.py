import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel

from voc_builder.exceptions import OpenAIServiceError
from voc_builder.models import (
    LiveStoryInfo,
    LiveTranslationInfo,
    TranslationResult,
    WordChoice,
    WordSample,
)
from voc_builder.store import get_internal_state_store

logger = logging.getLogger()


# Param: content
StreamHandler = Callable[[str], Any]


class WordChoiceModelResp(BaseModel):
    """The word returned by LLM service"""

    word: str
    word_normal: str
    word_meaning: str
    pronunciation: str

    def model_post_init(self, __context):
        self.word = self.word.lower()


async def get_translation(text: str, live_info: LiveTranslationInfo) -> TranslationResult:
    """Get the translated content of the given text.

    :param text: The text which needs to be translated.
    :param live_info: The info object which will be updated in the midway.
    :return: The translation result object.
    :raise VocBuilderError: when unable to finish the API call or reply is malformed.
    """

    def handle_stream_content(text: str):
        """Extract "translated" and updated the live_info object"""
        live_info.translated_text = text

    try:
        reply = await query_translation(text, stream_handler=handle_stream_content)
    except Exception as e:
        raise OpenAIServiceError("Error querying OpenAI API: %s" % e)
    finally:
        # Mark current info object as finished
        live_info.is_finished = True
    try:
        return TranslationResult(text=text, translated_text=reply)
    except ValueError as e:
        raise OpenAIServiceError(e)


# The prompt being used to translate text
prompt_main_system = """\
You are a translation assistant, I will give you a paragraph of english, please \
translate it into simplified Chinese, the answer should only include the translated \
content and have no extra content.
"""  # noqa: E501

prompt_main_user_tmpl = """\
The paragraph is:

{text}
"""


async def query_translation(text: str, stream_handler: Optional[StreamHandler] = None) -> str:
    """Query OpenAI to get the translation.

    :param stream_handler: A callback function to handle partial replies.
    :return: Translated text.
    """
    user_content = prompt_main_user_tmpl.format(text=text)
    prompt = prompt_main_system + "\n" + user_content
    agent = Agent(create_ai_model())
    message = ""
    async with agent.run_stream(prompt) as result:
        async for message in result.stream():
            if stream_handler:
                stream_handler(message)
    return message


async def get_uncommon_word(text: str, known_words: Set[str]) -> WordChoice:
    """Get the most uncommon word in given text"""
    try:
        choices = await query_get_word_choices(text, known_words, limit=1)
    except Exception as e:
        raise OpenAIServiceError("Error querying OpenAI API: %s" % e)
    if not choices:
        raise OpenAIServiceError("reply contains no word")
    # NOTE: The replay might contains multiple words, but we only return the first one
    # instead of raising an error.
    return WordChoice(**choices[0].dict())


# This default limit of how many new words to extract from the text
DEFAULT_NEW_WORDS_LIMIT = 4


def get_word_choices(text: str, known_words: Set[str]) -> List[WordChoice]:
    """Get a choices of words in given text"""
    try:
        reply = query_get_word_choices(text, known_words, limit=DEFAULT_NEW_WORDS_LIMIT)
    except Exception as e:
        raise OpenAIServiceError("Error querying OpenAI API: %s" % e)
    try:
        return parse_word_choices_reply(reply)
    except ValueError as e:
        raise OpenAIServiceError(e)


async def get_word_manually(text: str, word: str) -> WordChoice:
    """Get a word that is manually selected by user."""
    try:
        item = await query_get_word_manually(text, word)
    except Exception as e:
        raise OpenAIServiceError("Error querying OpenAI API: %s" % e)
    return WordChoice(**item.dict())


# The prompt being used to extract multiple words
prompt_word_choices_system = """You are a translation assistant, I will give you a \
paragraph of english and a list of words called "known-words" which is divided by ",", \
please find out the top {limit} rarely used word in the paragraph(the word must not \
in "known-words"). Reply the word, the normal form, the simplified Chinese meaning and \
the pronunciation of each word.
"""  # noqa: E501

prompt_word_choices_user_tmpl = """\
known-words: {known_words}

The paragraph is:

{text}"""

prompt_word_manually_system = """You are a translation assistant, I will give you a \
paragraph of english and a word in the paragraph. Reply the word, the normal form, \
the simplified Chinese meaning and the pronunciation of the word."""  # noqa: E501


prompt_word_manually_user_tmpl = """\
The paragraph is:

{text}

The word is: {word}"""


async def query_get_word_choices(text: str, known_words: Set[str], limit: Optional[int] = 3) -> str:
    """Query OpenAI to get the translation results.

    :param limit: The maximum number of words to return, default to 3
    :return: Well formatted string contains word and meaning
    """
    user_content = prompt_word_choices_user_tmpl.format(text=text, known_words=",".join(known_words))
    prompt = prompt_word_choices_system.format(limit=limit) + "\n" + user_content
    agent = Agent(create_ai_model(), result_type=List[WordChoiceModelResp])
    result = await agent.run(prompt)
    return result.data


async def query_get_word_manually(text: str, word: str) -> WordChoice:
    """Query OpenAI to get the meaning of manually selected word.

    :return: Well formatted string contains word and meaning.
    """
    user_content = prompt_word_manually_user_tmpl.format(text=text, word=word)
    prompt = prompt_word_manually_system + user_content
    agent = Agent(create_ai_model(), result_type=WordChoiceModelResp)
    result = await agent.run(prompt)
    return result.data


def parse_word_choices_reply(reply_text: str) -> List[WordChoice]:
    """Parse the OpenAI reply, extract uncommon words

    :param reply_text: Formatted text
    :return: A list of WordChoice object
    :raise: ValueError when the given reply text can not be parsed
    """
    return WordChoicesParser().parse(reply_text)


class WordChoicesParser:
    """Parser for getting the word choices from OpenAI API's reply"""

    def parse(self, reply_text: str) -> List[WordChoice]:
        fields_list = self._get_choice_fields_list(reply_text)

        # Validate the choice dict and convert to WordChoice object
        choices: List[WordChoice] = []
        for d in fields_list:
            try:
                choices.append(WordChoice(**d))
            except TypeError:
                raise ValueError(f"Invalid word choice dict: {d}")

        # The word was surrounded by {} sometimes, remove
        for c in choices:
            c.word = c.word.strip("{}").lower()
        return choices

    def _get_choice_fields_list(self, reply_text: str) -> List[Dict[str, str]]:
        """Get a list of word choice fields by parsing the reply text"""
        # Get all of the key value pairs from text first
        raw_items: List[Tuple[str, str]] = []
        for line in reply_text.split("\n"):
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip(" -").lower()
            raw_items.append((key, value.strip()))

        choices_dicts: List[Dict[str, str]] = []
        current_choice = None
        for key, value in raw_items:
            # The reply may use non-standard keys sometimes
            if key in ["word", "unknown-word", "unknown word"]:
                # Word has changed, push last word in to result list
                if current_choice:
                    choices_dicts.append(current_choice)

                current_choice = {"word": value}
            if not current_choice:
                continue
            if key == "meaning":
                current_choice["word_meaning"] = value
            elif key == "normal_form":
                current_choice["word_normal"] = value
            elif key == "pronunciation":
                current_choice["pronunciation"] = value

        # Push the last word in to result list
        if current_choice:
            choices_dicts.append(current_choice)
        return choices_dicts


# The prompt being used to generate stroy from words
prompt_write_story_user_tmpl = """\
Please write a short story which is less than 200 words, the story should use simple words and these special words must be included: {words}. Also surround every special word with a single "$" character at the beginning and the end.
"""  # noqa: E501


def get_story(words: List[WordSample], live_info: LiveStoryInfo) -> str:
    """Query OpenAI to get a story.

    :param live_info: The info object which represents the writing procedure
    :return: The story text
    :raise: OpenAIServiceError
    """
    _received = ""

    def handle_stream_content(text: str):
        nonlocal _received
        _received += text
        live_info.story_text = _received

    # Try to use the normal form of each word
    str_words = [w.word_normal or w.word for w in words]
    try:
        return query_story(str_words, stream_handler=handle_stream_content)
    except Exception as e:
        raise OpenAIServiceError("Error querying OpenAI API: %s" % e)
    finally:
        # Ends the live procedure
        live_info.is_finished = True


def query_story(words: List[str], stream_handler: Optional[StreamHandler] = None) -> str:
    """Query OpenAI API to get a story.

    :param stream_handler: A callback function to handle partial replies.
    :return: The story text
    """
    content = ""

    # Try to use the normal form of each word
    words_str = ",".join(words)
    user_content = prompt_write_story_user_tmpl.format(words=words_str)
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        stream=True,
        messages=[
            # Use a single "user" message at this moment because "system" role doesn't perform better
            {"role": "user", "content": user_content},
        ],
    )
    for part in completion:
        logger.debug("Completion API returns: %s", part)
        delta = part.choices[0].delta
        delta_content = delta.get("content")
        if delta_content:
            if stream_handler:
                stream_handler(delta_content)
            content += delta_content
    return content


def create_ai_model():
    """Create the model object for interacting with LLM service.

    :raise ValueError: when the system settings is invalid .
    """
    settings = get_internal_state_store().get_system_settings()
    if not settings:
        raise ValueError("System settings not found")

    if settings.model_provider == "openai":
        openai_config = settings.openai_config
        client = AsyncOpenAI(api_key=openai_config.api_key, base_url=openai_config.api_host or None)
        return OpenAIModel(openai_config.model, openai_client=client)
    elif settings.model_provider == "gemini":
        gemini_config = settings.gemini_config
        if gemini_config.api_host:
            extra_kwargs = {"url_template": str(gemini_config.api_host).rstrip("/") + "/v1beta/models/{model}:"}
        else:
            extra_kwargs = {}
        return GeminiModel(gemini_config.model, api_key=gemini_config.api_key, **extra_kwargs)  # type: ignore
    else:
        raise ValueError("Unknown model provider")
