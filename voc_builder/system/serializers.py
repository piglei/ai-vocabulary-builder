"""Serializers for system"""

from typing import Any, Dict, Literal, Union

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from voc_builder.system.constants import ModelProvider, TargetLanguage


class SettingsInput(BaseModel):
    """The input data for saving system settings"""

    target_language: str
    model_provider: str
    openai_config: Dict[str, Any]
    gemini_config: Dict[str, Any]
    anthropic_config: Dict[str, Any]

    @field_validator("target_language")
    @classmethod
    def validate_target_language(cls, value):
        if not value:
            raise ValueError("target language is required")
        if not TargetLanguage.get_by_code(value):
            raise ValueError(f"invalid target language: {value}")
        return value

    @field_validator("model_provider")
    @classmethod
    def validate_model_provider(cls, value):
        try:
            ModelProvider(value)
        except ValueError:
            raise ValueError("invalid model provider")
        return value


class OpenAIConfigInput(BaseModel):
    api_key: str = Field(..., min_length=1)
    api_host: Union[AnyHttpUrl, Literal[""]]
    model: str

    @field_validator("model")
    @classmethod
    def validate_model(cls, value):
        if not value:
            raise ValueError("model is required")
        return value


class GeminiConfigInput(BaseModel):
    api_key: str = Field(..., min_length=1)
    api_host: Union[AnyHttpUrl, Literal[""]]
    model: str

    @field_validator("model")
    @classmethod
    def validate_model(cls, value):
        if not value:
            raise ValueError("model is required")
        return value


class AnthropicConfigInput(BaseModel):
    api_key: str = Field(..., min_length=1)
    api_host: Union[AnyHttpUrl, Literal[""]]
    model: str

    @field_validator("model")
    @classmethod
    def validate_model(cls, value):
        if not value:
            raise ValueError("model is required")
        return value
