"""Common fixtures for API tests."""

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import ValidationError

from voc_builder.builder.views import router as builder_router
from voc_builder.common.errors import (
    api_error_exception_handler,
    pydantic_exception_handler,
    req_validation_exception_handler,
)
from voc_builder.common.web.std_err import APIError
from voc_builder.learn.views import router as learn_router
from voc_builder.system.views import router as system_router


@pytest.fixture()
def client():
    app = FastAPI()
    app.add_exception_handler(ValidationError, pydantic_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, req_validation_exception_handler)  # type: ignore
    app.add_exception_handler(APIError, api_error_exception_handler)  # type: ignore
    # Routers
    app.include_router(builder_router)
    app.include_router(learn_router)
    app.include_router(system_router)
    return TestClient(app)
