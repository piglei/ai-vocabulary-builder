from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


async def pydantic_exception_handler(request: Request, exc: ValidationError):
    """Custom exception handler for Pydantic validation errors"""
    msg = ",".join([e["msg"] for e in exc.errors()])
    return JSONResponse(
        status_code=400,
        content={"error": "validation_error", "message": msg},
    )


async def req_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom exception handler for request validation errors"""
    msg = ",".join([e["msg"] for e in exc.errors()])
    return JSONResponse(
        status_code=400,
        content={"error": "validation_error", "message": msg},
    )
