from typing import Any

from src.base.domain.entity import BaseEntity


class BaseDomainException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)


class NotFoundException(BaseDomainException):
    def __init__(
        self,
        detail: Any = None,
        entity: BaseEntity | type[BaseEntity] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if entity and not detail:
            entity_name = (
                entity.__class__.__name__
                if isinstance(entity, BaseEntity)
                else getattr(entity, "__name__", "Resource")
            )
            detail = f"{entity_name} not found"
        super().__init__(status_code=404, detail=detail, headers=headers)


class BadRequestException(BaseDomainException):
    def __init__(
        self,
        detail: Any = "Bad request",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=400, detail=detail, headers=headers)


class UnauthorizedException(BaseDomainException):
    def __init__(
        self,
        detail: Any = "Unauthorized",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=401, detail=detail, headers=headers)


class ForbiddenException(BaseDomainException):
    def __init__(
        self,
        detail: Any = "Forbidden",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=403, detail=detail, headers=headers)


class ConflictException(BaseDomainException):
    def __init__(
        self,
        detail: Any = "Conflict",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=409, detail=detail, headers=headers)


class UnprocessableEntityException(BaseDomainException):
    def __init__(
        self,
        detail: Any = "Unprocessable entity",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=422, detail=detail, headers=headers)


class TooManyRequestsException(BaseDomainException):
    def __init__(
        self,
        detail: Any = "Too many requests",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=429, detail=detail, headers=headers)


class UpstreamServiceException(BaseDomainException):
    def __init__(
        self,
        status_code: int = 502,
        detail: Any = "Upstream service error",
    ):
        super().__init__(status_code, detail)


class BadGatewayException(UpstreamServiceException):
    def __init__(self, detail: Any = "Bad gateway"):
        super().__init__(status_code=502, detail=detail)


class ServiceUnavailableException(UpstreamServiceException):
    def __init__(self, detail: Any = "Service unavailable"):
        super().__init__(status_code=503, detail=detail)


class GatewayTimeoutException(UpstreamServiceException):
    def __init__(self, detail: Any = "Gateway timeout"):
        super().__init__(status_code=504, detail=detail)
