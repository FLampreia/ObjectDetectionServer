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


