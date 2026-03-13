from fastapi import FastAPI, status

from app.exceptions.base import create_exception_handler
from app.exceptions.custom_exceptions import EmailAlreadyExists, UsernameAlreadyExists, DatabaseIntegrityException


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