from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.base.exceptions import UnauthorizedException
from src.users.ports.security.jwt import JwtPort


@dataclass(frozen=True)
class JwtSettings:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


class JoseJwtService(JwtPort):
    def __init__(self, settings: JwtSettings) -> None:
        self._s = settings

    def create_access_token(
        self,
        *,
        subject: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=self._s.access_token_expire_minutes)

        claims: dict[str, Any] = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        if extra_claims:
            claims.update(extra_claims)

        return jwt.encode(claims, self._s.secret_key, algorithm=self._s.algorithm)

    def decode(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token, self._s.secret_key, algorithms=[self._s.algorithm]
            )
            return dict(payload)
        except (JWTError, ValueError, TypeError) as e:
            raise UnauthorizedException("Invalid or expired token") from e
