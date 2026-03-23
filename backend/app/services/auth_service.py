from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings
import hashlib
from typing import Union
import bcrypt


def _prepare_for_bcrypt_bytes(password: Union[str, bytes]) -> bytes:
    """Return bytes safe for bcrypt (<=72 bytes). If input is longer than
    72 bytes, return the SHA-256 hex string encoded as UTF-8 (64 bytes).
    """
    if isinstance(password, str):
        pw_bytes = password.encode("utf-8")
    else:
        pw_bytes = password

    if len(pw_bytes) > 72:
        return hashlib.sha256(pw_bytes).hexdigest().encode("utf-8")
    return pw_bytes


def _prepare_for_bcrypt_sha256_bytes(password: Union[str, bytes]) -> bytes:
    """Return the SHA-256 hex (utf-8) of the password (used by bcrypt_sha256).
    This matches Passlib's bcrypt_sha256 behavior for interoperability.
    """
    if isinstance(password, str):
        pw_bytes = password.encode("utf-8")
    else:
        pw_bytes = password
    return hashlib.sha256(pw_bytes).hexdigest().encode("utf-8")


def get_password_hash(password: str) -> str:
    """Create a bcrypt hash for a password while supporting long inputs.

    Uses the `bcrypt` library directly and pre-hashes inputs >72 bytes.
    """
    pw_bytes = _prepare_for_bcrypt_bytes(password)
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a stored hash.

    Tries several verification strategies for compatibility:
    1) bcrypt using pre-hash-if-too-long (how new hashes are created)
    2) bcrypt_sha256 (pre-hash-with-sha256 unconditionally)
    3) legacy bcrypt created by truncating to 72 bytes
    """
    # normalize stored hash to bytes
    stored = hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password

    # 1) direct bcrypt using pre-hash-if-too-long
    try:
        pw_prepared = _prepare_for_bcrypt_bytes(plain_password)
        if bcrypt.checkpw(pw_prepared, stored):
            return True
    except Exception:
        pass

    # 2) bcrypt_sha256 style (always pre-hash with sha256 hex)
    try:
        pw_sha256 = _prepare_for_bcrypt_sha256_bytes(plain_password)
        if bcrypt.checkpw(pw_sha256, stored):
            return True
    except Exception:
        pass

    # 3) legacy truncated-to-72-bytes bcrypt hashes
    try:
        pw_bytes = plain_password.encode("utf-8") if isinstance(plain_password, str) else plain_password
        legacy = pw_bytes[:72]
        if bcrypt.checkpw(legacy, stored):
            return True
    except Exception:
        pass

    return False

def create_access_token(subject: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return int(payload["sub"])
