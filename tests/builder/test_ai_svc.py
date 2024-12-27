from types import SimpleNamespace
from unittest import mock

import pytest

from voc_builder.builder.ai_svc import (
    ManuallyWordQuerier,
    RareWordQuerier,
    WordChoiceModelResp,
)
from voc_builder.exceptions import AIServiceError
from voc_builder.infras.ai import AIResultMode

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


@pytest.mark.asyncio
class TestRareWordQuerierJsonResult:
    @pytest.mark.parametrize(
        "data",
        [
            # The API sometimes returns the JSON string with triple quotes
            f"""```json\n{VALID_JSON_REPLY}\n```""",
            VALID_JSON_REPLY,
        ],
    )
    @mock.patch("voc_builder.builder.ai_svc.JsonWordDefGetter.agent_request")
    async def test_json_valid_response(self, mocker, data):
        mocker.return_value = SimpleNamespace(data=data)

        word = await RareWordQuerier(None, result_mode=AIResultMode.JSON).query(
            "The team's synergy was evident in their performance.",
            set(),
            "Simplified Chinese",
        )

        # Check the prompt
        prompt = mocker.call_args[0][1]
        assert all(
            keyword in prompt.system
            for keyword in [
                "rarely encountered word",
                "JSON OUTPUT",
                "List all possible definitions",
            ]
        )
        assert all(keyword in prompt.user for keyword in ["Word List:", "synergy"])

        # Check the word object
        assert word.word == "synergy"
        assert word.definitions == ["[noun] 协同作用，协同效应"]

    @mock.patch("voc_builder.builder.ai_svc.JsonWordDefGetter.agent_request")
    async def test_invalid_response(self, mocker):
        mocker.return_value = SimpleNamespace(data="not a valid json")

        with pytest.raises(AIServiceError):
            await RareWordQuerier(None, result_mode=AIResultMode.JSON).query(
                "The team's synergy was evident in their performance.",
                set(),
                "Simplified Chinese",
            )


@pytest.mark.asyncio
class TestRareWordQuerierPydanticResult:
    @mock.patch("voc_builder.builder.ai_svc.PydanticWordDefGetter.agent_request")
    async def test_normal(self, mocker):
        mocker.return_value = SimpleNamespace(data=VALID_PYDANTIC_REPLY)

        word = await RareWordQuerier(None, result_mode=AIResultMode.PYDANTIC).query(
            "The team's synergy was evident in their performance.",
            set(),
            "Simplified Chinese",
        )

        # Check the prompt
        prompt = mocker.call_args[0][1]
        assert all(
            keyword in prompt.system
            for keyword in [
                "rarely encountered word",
                "List all possible definitions",
            ]
        )
        assert all(keyword in prompt.user for keyword in ["Word List:", "synergy"])
        assert "JSON OUTPUT" not in prompt.system

        # Check the word object
        assert word.word == "synergy"
        assert word.definitions == ["[noun] 协同作用，协同效应"]


@pytest.mark.asyncio
class TestManuallyWordQuerierJSONResult:
    @mock.patch("voc_builder.builder.ai_svc.JsonWordDefGetter.agent_request")
    async def test_valid_json_result(self, mocker):
        data = f"""```json\n{VALID_JSON_REPLY}\n```"""
        mocker.return_value = SimpleNamespace(data=data)

        word = await ManuallyWordQuerier(None, result_mode=AIResultMode.JSON).query(
            "The team's synergy was evident in their performance.",
            "synergy",
            "Simplified Chinese",
        )

        # Check the prompt
        prompt = mocker.call_args[0][1]
        assert all(
            keyword in prompt.system
            for keyword in [
                "an english word",
                "JSON OUTPUT",
                "List all possible definitions",
            ]
        )
        assert all(keyword in prompt.user for keyword in ["Word:", "synergy"])

        # Check the word object
        assert word.word == "synergy"
        assert word.definitions == ["[noun] 协同作用，协同效应"]


@pytest.mark.asyncio
class TestManuallyWordQuerierPydanticResult:
    @mock.patch("voc_builder.builder.ai_svc.PydanticWordDefGetter.agent_request")
    async def test_valid_pydantic_result(self, mocker):
        mocker.return_value = SimpleNamespace(data=VALID_PYDANTIC_REPLY)

        word = await ManuallyWordQuerier(None, result_mode=AIResultMode.PYDANTIC).query(
            "The team's synergy was evident in their performance.",
            "synergy",
            "Simplified Chinese",
        )

        # Check the prompt
        prompt = mocker.call_args[0][1]
        assert all(
            keyword in prompt.system
            for keyword in [
                "an english word",
                "List all possible definitions",
            ]
        )
        assert "JSON OUTPUT" not in prompt.system
        assert all(keyword in prompt.user for keyword in ["Word:", "synergy"])

        # Check the word object
        assert word.word == "synergy"
        assert word.definitions == ["[noun] 协同作用，协同效应"]
