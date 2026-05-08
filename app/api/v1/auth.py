import logging
import uuid
from datetime import timedelta
from fastapi.responses import JSONResponse
from app.core.config import config
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from app.api.deps import get_user_service, get_current_user, get_current_token_payload
from app.core.redis_config import redis_client, add_jti_to_blocklist
from app.core.security import create_access_token, decode_token
from app.db.database import SessionLocal, get_db
from app.exceptions.custom_exceptions import InvalidCredentials, InvalidToken, InvalidSession
from app.models.auth import RefreshRequest
from app.models.user import UserRead, UserLogin, UserCreate
from app.services.user_service import UserService

auth_router = APIRouter()
logger = logging.getLogger(__name__)

@auth_router.post("/signin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_account(
        user: UserCreate,
        service: UserService = Depends(get_user_service),
):
    logger.info("Creating user with data: %s", user)
    return service.create_user(user.username, user.password, user.email, user.full_name)


@auth_router.post("/login", response_model=UserRead, status_code=status.HTTP_200_OK)
async def login(
        user: UserLogin,
        service: UserService = Depends(get_user_service)
):
    logger.info("Trying to logging user with data: %s", user)

    # Verify is credentials are valid
    if not service.verify_login(user.email, user.password):
        raise InvalidCredentials()

    logged_user = service.get_user_by_email(user.email)


    logger.info("Logged in user with data: %s", user)

    access_token = create_access_token(
        user_data={
            'email': logged_user.email,
            'user_id': str(logged_user.id),
            'role': getattr(logged_user.role, "value", None)
        }
    )

    refresh_token = create_access_token(
        user_data={
            'email': logged_user.email,
            'user_id': str(logged_user.id)
        },
        refresh=True,
        expires_delta=timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return JSONResponse(
        content={
            "message": "Login Successful",
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    )


@auth_router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def me (
        current_user = Depends(get_current_user)
):
    return current_user

@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
        current_token_payload = Depends(get_current_token_payload)
):
    jti = current_token_payload.get("jti")

    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={
            "message": "Successfully logged out"
        }
    )

