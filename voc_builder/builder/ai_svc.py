import logging
from typing import AsyncGenerator, List, Set

from pydantic import BaseModel
from pydantic_ai import Agent

from voc_builder.builder.models import WordChoice
from voc_builder.common.text import get_word_candidates
from voc_builder.exceptions import AIServiceError

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


# The prompt being used to extract multiple words
prompt_rare_word_system = """You are a english reading specialist, I will give you a list \
of english words separated by ",", please find the most rarely encountered word as the result. \

Reply the result word, the base form, the {language} definition and \
the pronunciation of the result word.

- List all possible definitions, separated by "$", with each formatted as \
"[{{part of speech(adj/noun/...)}}] {{ {language} definition }}".
    - Example: [noun] {language} definition1 $ [verb] {language} definition2
- A paragraph will be given as a reference because there might be homographs.
"""  # noqa: E501


prompt_rare_word_user_tmpl = """\
Words: {words}

Paragraph for reference: {text}
"""


async def get_rare_word(
    model, text: str, known_words: Set[str], language: str
) -> WordChoice:
    """Get the most rarely word in given text."""
    words = get_word_candidates(text, known_words=known_words)
    if not words:
        raise AIServiceError("Text does not contain any words that meet the criteria")

    user_content = prompt_rare_word_user_tmpl.format(text=text, words=", ".join(words))
    prompt = prompt_rare_word_system.format(language=language) + user_content
    agent: Agent = Agent(model, result_type=WordChoiceModelResp)
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

Reply the word, the base form, the {language} definition and the \
pronunciation of the word.

- List all possible definitions, separated by "$", with each formatted as \
"[{{part of speech(adj/noun/...)}}] {{ {language} definition }}".
    - Example: [noun] {language} definition1 $ [verb] {language} definition2
- A paragraph will be given as a reference because there might be homographs.
"""  # noqa: E501


prompt_word_manually_user_tmpl = """\
Word: {word}

Paragraph for reference: {text}
"""


async def get_word_manually(model, text: str, word: str, language: str) -> WordChoice:
    """Get a word that is manually selected by user.

    :param text: The text which contains the word.
    :param word: The selected word.
    :raise: AIServiceError
    """
    user_content = prompt_word_manually_user_tmpl.format(text=text, word=word)
    prompt = prompt_word_manually_system.format(language=language) + user_content
    agent: Agent = Agent(model, result_type=WordChoiceModelResp)
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
