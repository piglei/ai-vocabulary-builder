import logging
from typing import AsyncGenerator, List

from pydantic_ai import Agent

from voc_builder.builder.models import WordSample
from voc_builder.exceptions import AIServiceError

logger = logging.getLogger()


async def get_story(model, words: List[WordSample]) -> AsyncGenerator[str, None]:
    """Query AI backend API to get a story.

    :param live_info: The info object which represents the writing procedure
    :return: The story text
    :raise: AIServiceError
    """
    # Try to use the normal form of each word
    str_words = [w.word_normal or w.word for w in words]
    try:
        async for message in query_story(model, str_words):
            yield message
    except Exception as e:
        raise AIServiceError("Error calling AI backend API: %s" % e)


# The prompt being used to generate stroy from words
prompt_write_story_user_tmpl = """\
Please write a short story which is less than {total_words_cnt} words, the story should use simple \
words and these special words must be included: {words}.  Also surround every special word \
with a single "$" character at the beginning and the end.

- Use paragraphs to improve readability.
"""  # noqa: E501


async def query_story(model, words: List[str]) -> AsyncGenerator[str, None]:
    """Query AI backend API to get a story.

    :param stream_handler: A callback function to handle partial replies.
    :return: The story text
    """
    words_str = ",".join(words)
    prompt = prompt_write_story_user_tmpl.format(
        words=words_str, total_words_cnt=len(words) * 30
    )
    agent: Agent = Agent(model)
    async with agent.run_stream(prompt) as result:
        async for message in result.stream():
            yield message
