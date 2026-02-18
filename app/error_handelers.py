import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import httpx
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.base.exceptions import (
    BaseDomainException,
    ConflictException,
    BadGatewayException,
    NotFoundException,
    ServiceUnavailableException,
    GatewayTimeoutException,
    UnprocessableEntityException,
)

logger = logging.getLogger("uvicorn.error")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseDomainException)
    async def handle_base_domain_exc(_: Request, exc: BaseDomainException):
        logger.warning("BaseDomainException: %s", exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def handle_fastapi_validation(_: Request, exc: RequestValidationError):
        logger.warning("RequestValidationError: %s", exc)
        return JSONResponse(
            status_code=UnprocessableEntityException().status_code,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(ValidationError)
    async def handle_pydantic_validation(_: Request, exc: ValidationError):
        logger.warning("Pydantic ValidationError: %s", exc)
        return JSONResponse(
            status_code=UnprocessableEntityException().status_code,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity(_: Request, exc: IntegrityError):
        logger.exception("IntegrityError")
        return JSONResponse(
            status_code=ConflictException().status_code,
            content={"detail": "Conflict: integrity constraint violated"},
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy(_: Request, exc: SQLAlchemyError):
        logger.exception("SQLAlchemyError")
        return JSONResponse(status_code=500, content={"detail": "Database error"})

    @app.exception_handler(httpx.TimeoutException)
    async def handle_upstream_timeout(_: Request, exc: httpx.TimeoutException):
        logger.warning("Upstream timeout: %s", exc)
        return JSONResponse(
            status_code=GatewayTimeoutException().status_code,
            content={"detail": "Upstream request timed out"},
        )

    @app.exception_handler(httpx.ConnectError)
    async def handle_upstream_connect(_: Request, exc: httpx.ConnectError):
        logger.warning("Upstream connect error: %s", exc)
        return JSONResponse(
            status_code=ServiceUnavailableException().status_code,
            content={"detail": "Upstream service unavailable"},
        )

    @app.exception_handler(httpx.HTTPStatusError)
    async def handle_upstream_status(_: Request, exc: httpx.HTTPStatusError):
        code = exc.response.status_code
        logger.warning("Upstream HTTPStatusError: %s", code)
        if code == 502:
            return JSONResponse(status_code=502, content={"detail": "Bad gateway"})
        if code == 503:
            return JSONResponse(
                status_code=503, content={"detail": "Service unavailable"}
            )
        if code == 504:
            return JSONResponse(status_code=504, content={"detail": "Gateway timeout"})
        return JSONResponse(
            status_code=BadGatewayException().status_code,
            content={"detail": f"Upstream error ({code})"},
        )

    @app.exception_handler(NotFoundException)
    async def handle_not_found_http_exc(_: Request, exc: NotFoundException):
        logger.warning("NotFoundException: %s", exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        logger.exception("Unhandled exception")
        raise exc
