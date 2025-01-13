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
You are a helpful language tutor. Write a short and engaging story using the following words: \
{words}. In the story, these words should be used naturally, but other words should be simple, \
common, and easy for a beginner to understand. The story should be fun and interesting, making \
sure to keep the sentences short and clear. Avoid using difficult vocabulary, and make the story \
exciting enough to keep the reader’s attention while helping them learn new words.

1. Surround each special word with a single "$" character at the beginning and end.
2. Use paragraphs to improve readability.
3. The length of the story should be less than {total_words_cnt} words.
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
