from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from src.users.ports.security.password_hasher import PasswordHasherPort


class PasslibPasswordHasher(PasswordHasherPort):
    _pwd = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

    def is_hashed(self, value: str) -> bool:
        return self._pwd.identify(value) is not None

    def ensure_hashed(self, password: str) -> str:
        return password if self.is_hashed(password) else self._pwd.hash(password)

    def hash(self, password: str) -> str:
        return self._pwd.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self._pwd.verify(plain_password, hashed_password)
        except UnknownHashError:
            return False
