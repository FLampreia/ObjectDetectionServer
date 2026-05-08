import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.redis_config import token_in_blocklist
from app.db.database import get_db
from app.exceptions.custom_exceptions import UserNotFound, InvalidToken, RevokedToken
from app.services.user_service import UserService
from app.core.security import decode_token
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(session=db)


async def get_current_token_payload(
        token: str = Depends(oauth2_scheme),
):
    payload = decode_token(token)

    user_data = payload.get("user")
    jti = payload.get("jti")

    if not payload or not user_data or not jti:
        raise InvalidToken

    if await token_in_blocklist(jti):
        raise RevokedToken

    return {
        "user": user_data,
        "jti": jti,
        "refresh": payload.get("refresh", False),
        "exp": payload.get("exp")
    }


def get_current_user(
    payload = Depends(get_current_token_payload),
    service: UserService = Depends(get_user_service),
):

    user_id = UUID(payload["user"]["user_id"])

    user = service.get_user(user_id)

    if not user:
        raise UserNotFound()

    return user