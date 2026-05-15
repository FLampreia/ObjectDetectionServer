from fastapi import FastAPI, status

from app.exceptions.base import create_exception_handler
from app.exceptions.custom_exceptions import *

EXCEPTION_STATUS_MAP = {
    EmailAlreadyExists: status.HTTP_409_CONFLICT,
    UsernameAlreadyExists: status.HTTP_409_CONFLICT,
    DatabaseIntegrityException: status.HTTP_409_CONFLICT,
    EmailNotFound: status.HTTP_404_NOT_FOUND,
    InvalidToken: status.HTTP_401_UNAUTHORIZED,
    RevokedToken: status.HTTP_401_UNAUTHORIZED,
    InvalidSession: status.HTTP_401_UNAUTHORIZED,
    MalformedToken: status.HTTP_409_CONFLICT,
    RefreshTokenRequired: status.HTTP_401_UNAUTHORIZED,
    AccessTokenRequired: status.HTTP_401_UNAUTHORIZED,
    InsufficientPermission: status.HTTP_403_FORBIDDEN,
    UserNotFound: status.HTTP_404_NOT_FOUND,
    InvalidCredentials: status.HTTP_401_UNAUTHORIZED,
    RedisNotAvailable: status.HTTP_503_SERVICE_UNAVAILABLE,
    InvalidCurrentPassword: status.HTTP_400_BAD_REQUEST,
    UserAlreadyInTeam: status.HTTP_409_CONFLICT,
    NotTeamOwner: status.HTTP_403_FORBIDDEN,
    NotAllowedToRemoveOwner: status.HTTP_403_FORBIDDEN,
    NotAllowedToUpdate: status.HTTP_403_FORBIDDEN,
    NoFieldsToUpdate: status.HTTP_400_BAD_REQUEST,
    NotAllowedToDelete: status.HTTP_403_FORBIDDEN,
    TeamNameAlreadyExists: status.HTTP_409_CONFLICT,
    TeamNotFound: status.HTTP_404_NOT_FOUND,
}


def register_all_exceptions(app: FastAPI):

    for exception, status_code in EXCEPTION_STATUS_MAP.items():
        app.add_exception_handler(
            exception,
            create_exception_handler(status_code=status_code)
        )