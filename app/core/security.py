import hashlib
from datetime import timedelta, datetime, timezone
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from app.core.config import config
import uuid
import logging
from typing import Literal

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def preprocess_password(password: str) -> str:

    # Hash SHA-256 (hexadecimal -> 64 chars)
    return hashlib.sha256(password.encode()).hexdigest()


def generate_password_hash(password: str) -> str:

    prehashed = preprocess_password(password)

    return password_context.hash(prehashed)

def verify_password(plain_password: str, hashed_password: str) -> bool:

    prehashed = preprocess_password(plain_password)

    return password_context.verify(prehashed, hashed_password)


def create_token(sub: str, expires_delta: timedelta = None, type: Literal["access", "refresh"] = "access", session_id: str = None):

    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        'sub': sub,
        'session_id': session_id,
        'exp': expire,
        'jti': str(uuid.uuid4()),
        'type': type
    }

    return jwt.encode(
        payload = payload,
        key = config.JWT_SECRET,
        algorithm = config.JWT_ALGORITHM
    )

def decode_token(token: str) -> dict:

    try:

        token_data = jwt.decode(
            jwt = token,
            key = config.JWT_SECRET,
            algorithms = [config.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "session_id", "jti", "type"]},
        )

        return token_data

    except PyJWTError:
        logging.debug("Token validation failed")
        return None
