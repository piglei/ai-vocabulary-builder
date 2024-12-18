"""Serializers for system"""

from typing import Any, Dict, Literal, Union

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from voc_builder.constants import ModelProvider


class SettingsInput(BaseModel):
    """The input data for saving system settings"""

    model_provider: str
    openai_config: Dict[str, Any]
    gemini_config: Dict[str, Any]

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
