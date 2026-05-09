from fastapi import FastAPI, status

from app.exceptions.base import create_exception_handler
from app.exceptions.custom_exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
    DatabaseIntegrityException,
    EmailNotFound,
    InvalidToken,
    RevokedToken,
    RefreshTokenRequired,
    AccessTokenRequired,
    InsufficientPermission, UserNotFound, InvalidCredentials, RedisNotAvailable, InvalidCurrentPassword, InvalidSession,
    MalformedToken
)


def register_all_exceptions(app: FastAPI):

    app.add_exception_handler(
        EmailAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_409_CONFLICT
        )
    )

    app.add_exception_handler(
        UsernameAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_409_CONFLICT
        )
    )

    app.add_exception_handler(
        DatabaseIntegrityException,
        create_exception_handler(
            status_code=status.HTTP_409_CONFLICT
        )
    )

    app.add_exception_handler(
        EmailNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND
        )
    )

    app.add_exception_handler(
        InvalidToken,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    )

    app.add_exception_handler(
        RevokedToken,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    )

    app.add_exception_handler(
        InvalidSession,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    )

    app.add_exception_handler(
        MalformedToken,
        create_exception_handler(
            status_code=status.HTTP_409_CONFLICT
        )
    )

    app.add_exception_handler(
        RefreshTokenRequired,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    )

    app.add_exception_handler(
        AccessTokenRequired,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    )

    app.add_exception_handler(
        InsufficientPermission,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    )

    app.add_exception_handler(
        UserNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND
        )
    )

    app.add_exception_handler(
        InvalidCredentials,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    )

    app.add_exception_handler(
        RedisNotAvailable,
        create_exception_handler(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    )

    app.add_exception_handler(
        InvalidCurrentPassword,
        create_exception_handler(
            status_code=status.HTTP_409_CONFLICT
        )
    )