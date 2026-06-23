"""
Security utilities – password hashing and JWT token management.

Usage
-----
  from app.utils.security import hash_password, verify_password
  from app.utils.security import create_access_token, decode_token
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# ── Password hashing ─────────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of a plain-text password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Parameters
    ----------
    data          : Payload dict (must include ``sub`` = username).
    expires_delta : Optional custom TTL; defaults to JWT_EXPIRE_MINUTES.

    Returns
    -------
    str : Encoded JWT string.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug("JWT created | sub=%s exp=%s", data.get("sub"), expire)
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.

    Returns
    -------
    dict : Decoded payload.

    Raises
    ------
    JWTError : If token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
