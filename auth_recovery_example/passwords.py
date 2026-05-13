from passlib.context import CryptContext
from passlib.exc import UnknownHashError

pwd = CryptContext(schemes=["argon2"], deprecated="auto")


class PasswordHasher:
    @staticmethod
    def hash(password: str) -> str:
        return pwd.hash(password)

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        try:
            return pwd.verify(password, hashed)
        except (UnknownHashError, ValueError, TypeError):
            return False
