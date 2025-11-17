from types import SimpleNamespace
from unittest import mock

import pytest

from voc_builder.builder.ai_svc import (
    JsonWordDefGetter,
    ManuallyWordQuerier,
    RareWordQuerier,
    WordChoiceModelResp,
)
from voc_builder.exceptions import AIServiceError
from voc_builder.infras.ai import AIResultMode, PromptText

# A valid JSON word reply
VALID_JSON_REPLY = """{
    "word": "synergy",
    "word_base_form": "synergy",
    "definitions": "[noun] 协同作用，协同效应",
    "pronunciation": "ˈsɪnərdʒi"
}"""

# A valid pydantic word reply
VALID_PYDANTIC_REPLY = WordChoiceModelResp(
    word="synergy",
    word_base_form="synergy",
    definitions="[noun] 协同作用，协同效应",
    pronunciation="ˈsɪnərdʒi",
)


@pytest.fixture(params=["rare_word", "manually_word"])
def word_querier_invoker(request, result_mode):
    """A fixture that return an invoker function to query a word using a word querier."""
    if request.param == "rare_word":

        async def _invoker():
            return await RareWordQuerier(None, result_mode=result_mode).query(
                "The team's synergy was evident in their performance.",
                set(),
                "Simplified Chinese",
            )

        return "rare_word", _invoker
    elif request.param == "manually_word":

        async def _invoker():
            return await ManuallyWordQuerier(None, result_mode=result_mode).query(
                "The team's synergy was evident in their performance.",
                "synergy",
                "Simplified Chinese",
            )

        return "manually_word", _invoker
    return None


# The key prompts for the different word queriers, will be used for assertion in the tests
KEY_PROMPT_BY_QUERIER = {
    "rare_word": {
        "system": ["less commonly used or more advanced in vocabulary"],
        "user": ["Word List(separated by ", "):"],
    },
    "manually_word": {
        "system": ["an English word"],
        "user": ["Word:"],
    },
}


@pytest.mark.asyncio
class TestDifferentWordQuerierJsonResult:
    @pytest.fixture()
    def result_mode(self):
        return AIResultMode.JSON

    @mock.patch("voc_builder.builder.ai_svc.JsonWordDefGetter.agent_request")
    async def test_json_valid_response(self, mocker, word_querier_invoker):
        querier_name, _invoker = word_querier_invoker
        mocker.return_value = SimpleNamespace(output=VALID_JSON_REPLY)

        word = await _invoker()
        # Check the prompt
        prompt = mocker.call_args[0][1]
        assert "A list of all possible" in prompt.system
        assert "JSON OUTPUT" in prompt.system

        assert_querier_key_prompts(prompt, querier_name)

        # Check the word object
        assert word.word == "synergy"
        assert word.definitions == ["[noun] 协同作用，协同效应"]


@pytest.mark.asyncio
class TestDifferentWordQuerierPydanticResult:
    @pytest.fixture()
    def result_mode(self):
        return AIResultMode.PYDANTIC

    @mock.patch("voc_builder.builder.ai_svc.PydanticWordDefGetter.agent_request")
    async def test_json_valid_response(self, mocker, word_querier_invoker):
        querier_name, _invoker = word_querier_invoker
        mocker.return_value = SimpleNamespace(output=VALID_PYDANTIC_REPLY)

        word = await _invoker()
        # Check the prompt
        prompt = mocker.call_args[0][1]
        assert "A list of all possible" in prompt.system
        assert "JSON OUTPUT" not in prompt.system

        assert_querier_key_prompts(prompt, querier_name)

        # Check the word object
        assert word.word == "synergy"
        assert word.definitions == ["[noun] 协同作用，协同效应"]


def assert_querier_key_prompts(prompt, querier_name):
    """Check the key prompts for the different word queriers."""
    key_system_prompt = KEY_PROMPT_BY_QUERIER[querier_name]["system"]
    assert all(keyword in prompt.system for keyword in key_system_prompt)

    key_user_prompt = KEY_PROMPT_BY_QUERIER[querier_name]["user"]
    assert all(keyword in prompt.user for keyword in key_user_prompt)


@pytest.mark.asyncio
class TestJsonWordDefGetter:
    @pytest.mark.parametrize(
        "data",
        [
            # The API sometimes returns the JSON string with triple quotes
            f"""```json\n{VALID_JSON_REPLY}\n```""",
            VALID_JSON_REPLY,
        ],
    )
    @mock.patch("voc_builder.builder.ai_svc.JsonWordDefGetter.agent_request")
    async def test_valid_response(self, mocker, data):
        mocker.return_value = SimpleNamespace(output=data)
        word = await JsonWordDefGetter().query(
            None, PromptText([], []), "Simplified Chinese"
        )
        assert word.word == "synergy"

    @mock.patch("voc_builder.builder.ai_svc.JsonWordDefGetter.agent_request")
    async def test_invalid_response(self, mocker):
        mocker.return_value = SimpleNamespace(output="not a valid json")

        with pytest.raises(AIServiceError):
            await JsonWordDefGetter().query(
                None, PromptText([], []), "Simplified Chinese"
            )
