import logging
import uuid
from datetime import timedelta
from fastapi.responses import JSONResponse
from app.core.config import config
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
# from app.api.deps import get_user_service, get_current_user, get_current_token_payload
from app.core.redis_config import redis_client, add_jti_to_blocklist, token_in_blocklist, revoke_session, \
    is_session_revoked
from app.core.security import create_token, decode_token
from app.core.token import get_user_service, get_current_user, AccessTokenBearer, RefreshTokenBearer
from app.db.database import SessionLocal, get_db
from app.exceptions.custom_exceptions import InvalidCredentials, InvalidToken, InvalidSession, MalformedToken, \
    RevokedToken
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

    session_id = str(uuid.uuid4())

    access_token = create_token(
        sub=str(logged_user.id),
        session_id=session_id
    )

    refresh_token = create_token(
        sub=str(logged_user.id),
        session_id=session_id,
        type="refresh",
        expires_delta=timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    logger.info("Logged in user with data: %s", user)

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
        token_details: dict = Depends(AccessTokenBearer())
):
    jti = token_details["jti"]
    session_id = token_details["session_id"]

    await add_jti_to_blocklist(jti)
    await revoke_session(session_id)

    return JSONResponse(
        content={
            "message": "Successfully logged out"
        }
    )

@auth_router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
        token_details: dict = Depends(RefreshTokenBearer())
):
    jti = token_details["jti"]
    sub = token_details["sub"]
    session_id = token_details["session_id"]

    if not jti or not sub or not session_id:
        raise MalformedToken()

    if await token_in_blocklist(jti): # if jti was used, revoke session, to protect from attack
        await revoke_session(session_id)
        raise RevokedToken()

    if await is_session_revoked(session_id):
        raise RevokedToken()

    await add_jti_to_blocklist(jti)

    new_access_token = create_token(
        sub=sub,
        session_id=session_id,
    )

    new_refresh_token = create_token(
        sub=sub,
        session_id=session_id,
        type="refresh",
        expires_delta=timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return JSONResponse(
        content={
            "message": "Refresh Successful",
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
    )
