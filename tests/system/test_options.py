import pytest
import requests

from voc_builder.system.constants import ModelProvider
from voc_builder.system.services.options import (
    ANTHROPIC_VERSION,
    ModelOptionsFetchError,
    build_models_request,
    fetch_model_options,
    parse_gemini_models,
    parse_openai_compatible_models,
)


def test_build_models_request_uses_provider_specific_defaults():
    url, headers, params = build_models_request(
        ModelProvider.OPENAI.value, "secret-key", ""
    )

    assert url == "https://api.openai.com/v1/models"
    assert headers == {"Authorization": "Bearer secret-key"}
    assert params == {}


def test_build_models_request_handles_anthropic_headers_and_custom_v1_host():
    url, headers, params = build_models_request(
        ModelProvider.ANTHROPIC.value, "secret-key", "https://custom.example/v1/"
    )

    assert url == "https://custom.example/v1/models"
    assert headers == {
        "anthropic-version": ANTHROPIC_VERSION,
        "x-api-key": "secret-key",
    }
    assert params == {}


def test_build_models_request_handles_gemini_api_key_param():
    url, headers, params = build_models_request(
        ModelProvider.GEMINI.value, "secret-key", ""
    )

    assert url == "https://generativelanguage.googleapis.com/v1beta/models"
    assert headers == {}
    assert params == {"key": "secret-key"}


def test_parse_gemini_models_keeps_generation_capable_entries():
    models = parse_gemini_models(
        {
            "models": [
                {
                    "name": "models/gemini-2.5-flash",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/text-embedding-004",
                    "supportedGenerationMethods": ["embedContent"],
                },
            ]
        }
    )

    assert models == ["gemini-2.5-flash"]


def test_parse_openai_compatible_models_ignores_malformed_items():
    models = parse_openai_compatible_models(
        {"data": [{"id": "gpt-4o-mini"}, {"object": "model"}, "bad-item"]}
    )

    assert models == ["gpt-4o-mini"]


def test_fetch_model_options_wraps_network_errors(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.ConnectTimeout("timed out")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(ModelOptionsFetchError, match="Failed to request"):
        fetch_model_options(ModelProvider.OPENAI.value, "secret-key", "")
