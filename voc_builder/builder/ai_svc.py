import logging
import re
from typing import Any, AsyncGenerator, List, Set

from pydantic import BaseModel
from pydantic_ai import Agent

from voc_builder.builder.models import WordChoice
from voc_builder.common.text import get_word_candidates
from voc_builder.exceptions import AIServiceError
from voc_builder.infras.ai import AIResultMode, PromptText

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


async def get_translation(model, text: str, language: str) -> AsyncGenerator[str, None]:
    """Get the translated text of the given text.

    :param text: The text which needs to be translated.
    :param language: The target language.
    :return: The translation text.
    :raise AIServiceError: when unable to finish the API call or reply is malformed.
    """

    try:
        async for translated_text in query_translation(model, text, language):
            yield translated_text
    except Exception as e:
        raise AIServiceError("Error calling AI backend API: %s" % e)


# The prompt being used to translate text
prompt_main_system = """\
You are a translation assistant, I will give you a paragraph of english, please \
translate it into {language}, the answer should only include the translated \
content and have no extra content.
"""

prompt_main_user_tmpl = """\
The paragraph is:

{text}
"""


async def query_translation(
    model, text: str, language: str
) -> AsyncGenerator[str, None]:
    """Query the AI to get the translation."""
    user_content = prompt_main_user_tmpl.format(text=text)
    prompt = prompt_main_system.format(language=language) + "\n" + user_content
    agent: Agent = Agent(model)

    async with agent.run_stream(prompt) as result:
        async for message in result.stream():
            yield message


class RareWordQuerier:
    """Query the AI to get the rare word."""

    prompt_system_tmpl = """\
You are a english reading specialist, I will give you a list \
of english words separated by ",", please find the most rarely encountered word."""

    prompt_user_tmpl = """\
Word List: {words}

Paragraph for reference: {text}"""

    def __init__(self, model, result_mode: AIResultMode):
        self.model = model
        self.result_mode = result_mode

    async def query(self, text: str, known_words: Set[str], language: str) -> WordChoice:
        """Query the most rarely word in the given text."""
        words = get_word_candidates(text, known_words=known_words)
        if not words:
            raise AIServiceError(
                "Text does not contain any words that meet the criteria"
            )

        prompt = PromptText(
            system_lines=[self.prompt_system_tmpl.format(language=language)],
            user_lines=[self.prompt_user_tmpl.format(text=text, words=", ".join(words))],
        )
        return await word_def_getter_factory(self.result_mode).query(
            self.model, prompt, language
        )


class ManuallyWordQuerier:
    """Get a word that is manually selected by user."""

    prompt_system_tmpl = (
        "You are a translation assistant, I will give you an english word."
    )

    prompt_user_tmpl = """\
Word: {word}

Paragraph for reference: {text}"""

    def __init__(self, model, result_mode: AIResultMode):
        self.model = model
        self.result_mode = result_mode

    async def query(self, text: str, word: str, language: str) -> WordChoice:
        """Query the manually selected word."""
        prompt = PromptText(
            system_lines=[self.prompt_system_tmpl.format(language=language)],
            user_lines=[self.prompt_user_tmpl.format(text=text, word=word)],
        )
        return await word_def_getter_factory(self.result_mode).query(
            self.model, prompt, language
        )


def word_def_getter_factory(result_mode: AIResultMode) -> "BaseWordDefGetter":
    if result_mode == AIResultMode.PYDANTIC:
        return PydanticWordDefGetter()
    elif result_mode == AIResultMode.JSON:
        return JsonWordDefGetter()
    raise ValueError("Invalid result getting mode")


class BaseWordDefGetter:
    """Base class for getting word definition."""

    prompt_word_extra_reqs = """\
- Reply the word, the base form, the {language} definition and \
the pronunciation of the word.
- List all possible definitions, separated by "$", with each formatted as \
"[{{part of speech(adj/noun/...)}}] {{ {language} definition }}".
    - Example: [noun] {language} definition1 $ [verb] {language} definition2
- A paragraph will be given as a reference because there might be homographs."""

    async def query(self, model, prompt: PromptText, language: str) -> WordChoice:
        """Query the AI to get the word definition.

        :param model: The AI model object.
        :param prompt: The prompt text, it should make the AI return a word.
        :param language: The language of the word definition.
        """
        raise NotImplementedError

    def _to_word_choice(self, item: WordChoiceModelResp) -> WordChoice:
        return WordChoice(
            word=item.word,
            word_normal=item.word_base_form,
            pronunciation=item.pronunciation,
            definitions=item.get_definition_list(),
        )


class JsonWordDefGetter(BaseWordDefGetter):
    """Get a word's definitions, AI agent return JSON result."""

    prompt_json_output = """\
output the result in JSON format.

EXAMPLE JSON OUTPUT:
{{
    "word": "...",
    "word_base_form": "...",
    "definitions": "...",
    "pronunciation": "..."
}}"""

    async def query(self, model, prompt: PromptText, language: str) -> WordChoice:
        prompt.system_lines.append(self.prompt_word_extra_reqs.format(language=language))
        prompt.system_lines.append(self.prompt_json_output)
        result = await self.agent_request(model, prompt)
        item = self._parse_json_output(result.data)
        return self._to_word_choice(item)

    async def agent_request(self, model, prompt: PromptText) -> Any:
        agent: Agent = Agent(model, system_prompt=prompt.system)
        try:
            return await agent.run(prompt.user)
        except Exception as e:
            raise AIServiceError("Error calling AI backend API: %s" % e)

    def _parse_json_output(self, data: str) -> WordChoiceModelResp:
        """Parse the JSON output to get the word object."""
        obj = re.search(r"{[\s\S]*}", data, flags=re.MULTILINE)
        if not obj:
            raise AIServiceError("Invalid JSON output")
        return WordChoiceModelResp.model_validate_json(obj.group())


class PydanticWordDefGetter(BaseWordDefGetter):
    """Get a word's definitions, AI agent return Pydantic result."""

    async def query(self, model, prompt: PromptText, language: str) -> WordChoice:
        """Query the word using Pydantic mode."""
        prompt.system_lines.append(self.prompt_word_extra_reqs.format(language=language))
        result = await self.agent_request(model, prompt)
        return self._to_word_choice(result.data)

    async def agent_request(self, model, prompt: PromptText) -> Any:
        agent: Agent = Agent(
            model, system_prompt=prompt.system, result_type=WordChoiceModelResp
        )
        try:
            return await agent.run(prompt.user)
        except Exception as e:
            raise AIServiceError("Error calling AI backend API: %s" % e)
