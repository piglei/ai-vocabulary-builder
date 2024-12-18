import logging
import pathlib

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.responses import FileResponse

from voc_builder.builder.views import router as builder_router
from voc_builder.learn.views import router as learn_router
from voc_builder.system.views import router as system_router

from ..common.errors import (
    api_error_exception_handler,
    pydantic_exception_handler,
    req_validation_exception_handler,
)
from ..common.web.std_err import APIError

logger = logging.getLogger(__name__)

ROOT_DIR = pathlib.Path(__file__).parent.resolve()

app = FastAPI()

app.add_exception_handler(ValidationError, pydantic_exception_handler)  # type: ignore
app.add_exception_handler(RequestValidationError, req_validation_exception_handler)  # type: ignore
app.add_exception_handler(APIError, api_error_exception_handler)  # type: ignore
app.mount("/assets", StaticFiles(directory=str(ROOT_DIR / "dist/assets")), name="assets")

app.include_router(builder_router)
app.include_router(learn_router)
app.include_router(system_router)


# TODO: Should we restrict the allowed origins?
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/app/{any_path:path}")
def index():
    return FileResponse(str(ROOT_DIR / "dist/index.html"))
