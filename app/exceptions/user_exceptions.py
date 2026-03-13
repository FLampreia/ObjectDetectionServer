from fastapi import FastAPI
from starlette import status

from app.exceptions.base import AppException, create_exception_handler


class EmailAlreadyExists(AppException):
    def __init__(self):
        super().__init__("Email already registered")


class UsernameAlreadyExists(AppException):
    def __init__(self):
        super().__init__("Username already registered")

class DatabaseIntegrityException(AppException):
    def __init__(self):
        super().__init__("Database integrity exception")


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