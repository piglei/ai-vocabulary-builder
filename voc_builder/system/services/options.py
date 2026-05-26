"""Model option discovery services."""

from typing import Any, Dict, List, Tuple

import requests

from voc_builder.system.constants import ModelProvider

OPENAI_API_HOST = "https://api.openai.com/v1"
GEMINI_API_HOST = "https://generativelanguage.googleapis.com"
ANTHROPIC_API_HOST = "https://api.anthropic.com"
DEEPSEEK_API_HOST = "https://api.deepseek.com"

ANTHROPIC_VERSION = "2023-06-01"
MODEL_OPTIONS_REQUEST_TIMEOUT = 15


class ModelOptionsFetchError(Exception):
    """Raised when provider model options cannot be fetched or parsed."""


def fetch_model_options(provider: str, api_key: str, api_host: str) -> List[str]:
    """Fetch available model identifiers from the selected provider."""
    url, headers, params = build_models_request(provider, api_key, api_host)

    try:
        provider_response = requests.get(
            url, headers=headers, params=params, timeout=MODEL_OPTIONS_REQUEST_TIMEOUT
        )
    except requests.RequestException as exc:
        raise ModelOptionsFetchError(
            f"Failed to request provider models: {exc}"
        ) from exc

    if not provider_response.ok:
        raise ModelOptionsFetchError(build_provider_error_message(provider_response))

    try:
        data = provider_response.json()
    except ValueError as exc:
        raise ModelOptionsFetchError("Provider returned a non-JSON response.") from exc

    models = parse_models(provider, data)
    if not models:
        raise ModelOptionsFetchError("No models were returned by the provider.")

    return models


def build_models_request(
    provider: str, api_key: str, api_host: str
) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """Build the provider-specific request for listing available models."""
    match provider:
        case ModelProvider.OPENAI.value:
            return (
                join_api_path(normalize_api_host(api_host, OPENAI_API_HOST), "models"),
                {"Authorization": f"Bearer {api_key}"},
                {},
            )
        case ModelProvider.GEMINI.value:
            base_url = normalize_api_host(api_host, GEMINI_API_HOST)
            models_path = "models" if base_url.endswith("/v1beta") else "v1beta/models"
            return join_api_path(base_url, models_path), {}, {"key": api_key}
        case ModelProvider.ANTHROPIC.value:
            base_url = normalize_api_host(api_host, ANTHROPIC_API_HOST)
            models_path = "models" if base_url.endswith("/v1") else "v1/models"
            return (
                join_api_path(base_url, models_path),
                {"anthropic-version": ANTHROPIC_VERSION, "x-api-key": api_key},
                {},
            )
        case ModelProvider.DEEPSEEK.value:
            return (
                join_api_path(normalize_api_host(api_host, DEEPSEEK_API_HOST), "models"),
                {"Authorization": f"Bearer {api_key}"},
                {},
            )
        case _:
            raise ModelOptionsFetchError(f"unsupported provider: {provider}")


def normalize_api_host(api_host: str, fallback: str) -> str:
    """Normalize provider base URL while preserving the user's custom host."""
    return str(api_host or fallback).rstrip("/")


def join_api_path(api_host: str, path: str) -> str:
    """Join a normalized API host and a provider path."""
    return f"{api_host}/{path.lstrip('/')}"


def parse_models(provider: str, data: Dict[str, Any]) -> List[str]:
    """Parse provider model-list responses into model identifiers."""
    match provider:
        case ModelProvider.GEMINI.value:
            return parse_gemini_models(data)
        case _:
            return parse_openai_compatible_models(data)


def parse_gemini_models(data: Dict[str, Any]) -> List[str]:
    """Parse Gemini models and keep only content-generation capable entries."""
    models = []
    for model in data.get("models", []):
        if not isinstance(model, dict):
            continue
        if "generateContent" not in model.get("supportedGenerationMethods", []):
            continue
        raw_name = model.get("name")
        if not isinstance(raw_name, str):
            continue
        name = raw_name.removeprefix("models/")
        if name:
            models.append(name)
    return sorted(models)


def parse_openai_compatible_models(data: Dict[str, Any]) -> List[str]:
    """Parse model IDs from OpenAI-compatible list-model responses."""
    models = []
    for model in data.get("data", []):
        if not isinstance(model, dict):
            continue
        model_id = model.get("id")
        if isinstance(model_id, str):
            models.append(model_id)
    return sorted(models)


def build_provider_error_message(response: requests.Response) -> str:
    """Extract a readable provider error without assuming a response schema."""
    try:
        data = response.json()
    except ValueError:
        return response.text or response.reason

    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if data.get("message"):
            return str(data["message"])
    return response.text or response.reason
