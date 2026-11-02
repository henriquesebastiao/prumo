import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()

# Verified against when the user does not exist, so that login takes the same time either way.
DUMMY_PASSWORD_HASH = _hasher.hash("prumo-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError, InvalidHashError:
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def new_token() -> str:
    """Opaque session token: 32 random bytes, URL-safe."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> bytes:
    """Only this SHA-256 digest is stored; the token itself never touches the database."""
    return hashlib.sha256(token.encode()).digest()
