from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .web.std_err import APIError, ErrorCode


class ErrorCodes:
    """Error codes for the API"""

    AI_SERVICE_ERROR = ErrorCode("AI service error")
    WORD_ALREADY_EXISTS = ErrorCode("The word already exists")
    EXACTING_WORD_FAILED = ErrorCode("Failed to exact the word")
    MANUALLY_SAVE_WORD_FAILED = ErrorCode("Failed to save the word")


# 实例化一个全局对象
error_codes = ErrorCodes()


async def pydantic_exception_handler(request: Request, exc: ValidationError):
    """Custom exception handler for Pydantic validation errors"""
    return JSONResponse(
        status_code=400,
        content={"code": "VALIDATION_ERROR", "message": str(exc)},
    )


async def req_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Custom exception handler for request validation errors"""
    return JSONResponse(
        status_code=400,
        content={"code": "VALIDATION_ERROR", "message": str(exc)},
    )


async def api_error_exception_handler(request: Request, exc: APIError):
    """Custom exception handler for Pydantic validation errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": exc.data},
    )
