import logging
import uuid
from datetime import timedelta
from fastapi.responses import JSONResponse
from app.core.config import config
from fastapi import APIRouter, Depends
from starlette import status
from app.services.redis_service import add_jti_to_blocklist, revoke_session, consume_refresh_token
from app.core.security import create_token
from app.core.token import get_user_service, get_current_user, LogoutTokenBearer, RefreshTokenBearer
from app.exceptions.custom_exceptions import InvalidCredentials, InvalidToken, MalformedToken, RevokedToken, UserNotFound
from app.models.token import TokenResponse
from app.models.user import UserRead, UserLogin, UserCreate
from app.services.user_service import UserService

auth_router = APIRouter()
logger = logging.getLogger(__name__)

@auth_router.post("/signin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
        user: UserCreate,
        service: UserService = Depends(get_user_service),
):
    logger.info("Creating user")
    return service.create_user(user.username, user.password, user.email, user.full_name)


@auth_router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
        user: UserLogin,
        service: UserService = Depends(get_user_service)
):
    logger.info("Attempting user login")

    # Verify if credentials are valid
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

    logger.info("User login succeeded")

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
        token_details: dict = Depends(LogoutTokenBearer())
):
    jti = token_details["jti"]
    session_id = token_details["session_id"]

    await add_jti_to_blocklist(jti, token_details["exp"])
    await revoke_session(session_id)

    return JSONResponse(
        content={
            "success": True
        }
    )

@auth_router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
        token_details: dict = Depends(RefreshTokenBearer()),
        service: UserService = Depends(get_user_service),
):
    jti = token_details["jti"]
    sub = token_details["sub"]
    session_id = token_details["session_id"]

    if not jti or not sub or not session_id:
        raise MalformedToken()

    try:
        user = service.get_user(uuid.UUID(sub))
    except (ValueError, UserNotFound):
        raise InvalidToken()
    if user is None:
        raise InvalidToken()

    if not await consume_refresh_token(jti, session_id, token_details["exp"]):
        raise RevokedToken()

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
