import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.exceptions.custom_exceptions import UserNotFound
from app.services.user_service import UserService
from app.core.security import decode_token
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(session=db)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service),
):

    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = UUID(payload["user"]["user_id"])

    user = service.get_user(user_id)

    if not user:
        raise UserNotFound()

    return user