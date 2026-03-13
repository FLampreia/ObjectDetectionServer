import logging
from typing import Any, Callable
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class AppException(Exception):
    """Base class for all exceptions in this application."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

def create_exception_handler(
        status_code: int
) -> Callable[[Request, Exception], JSONResponse ]:

    """Create the exception handler"""

    def exception_handler(request: Request, exc: AppException):

        logger.warning(
            "%s %s - %s",
            request.method,
            request.url.path,
            exc.message
        )

        return JSONResponse(
            status_code=status_code,
            content={"detail" : exc.message},
        )

    return exception_handler