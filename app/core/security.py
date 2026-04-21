import hashlib
from datetime import timedelta, datetime
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from app.core.config import config
import uuid
import logging

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


def create_access_token(user_data: dict, expires_delta: timedelta = None, refresh: bool = False):

    expire = datetime.now() + (
        expires_delta if expires_delta else timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {'user': user_data,
               'exp': expire,
               'jti': str(uuid.uuid4()),
               'refresh': refresh
               }

    token = jwt.encode(
        payload = payload,
        key = config.JWT_SECRET,
        algorithm = "HS256"
    )

    return token

def decode_token(token: str) -> dict:

    try:

        token_data = jwt.decode(
            jwt = token,
            key = config.JWT_SECRET,
            algorithms = "HS256"
        )

        return token_data

    except PyJWTError as e:
        logging.exception(e)
        return None
