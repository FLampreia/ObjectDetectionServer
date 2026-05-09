from fastapi import Request, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.core.deps import get_user_service
from app.core.redis_config import token_in_blocklist, is_session_revoked
from app.exceptions.custom_exceptions import (
    InvalidToken,
    RefreshTokenRequired,
    AccessTokenRequired,
    InsufficientPermission
)
from uuid import UUID
from app.db.schema import User
from app.db.database import get_db
from app.services.team_service import TeamService
from app.services.user_service import UserService
from app.core.security import decode_token


class TokenBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)


    async def __call__(
            self,
            request: Request
    ) -> dict:

        creds: HTTPAuthorizationCredentials = await super().__call__(request)

        token = creds.credentials
        token_data = decode_token(token)

        if token_data is None:
            raise InvalidToken()

        jti = token_data.get("jti")
        session_id = token_data.get("session_id")

        if not jti or not session_id:
            raise InvalidToken()

        if await token_in_blocklist(jti):
            raise InvalidToken()

        if await is_session_revoked(session_id):
            raise InvalidToken()

        self.verify_token_data(token_data)

        return token_data

    def verify_token_data(self, token_data):
        raise NotImplementedError("Please override this method in child classes")

class AccessTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict) -> None:
        if token_data.get("type") != "access":
            raise AccessTokenRequired()


class RefreshTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict) -> None:
        if token_data.get("type") != "refresh":
            raise RefreshTokenRequired()


def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    user_service: UserService = Depends(get_user_service)
) -> User:

    user_id = UUID(token_details["sub"])

    user = user_service.get_user(user_id)

    return user

#
# def get_current_roles(
#     token_details: dict = Depends(AccessTokenBearer())
# ) -> List[str]:
#
#     return token_details["user"]["roles"]


# TODO verificar a utilização de roles para aceder aos endpoints
# class RoleChecker:
#
#     def __init__(self, allowed_roles: List[str]):
#         self.allowed_roles = allowed_roles
#
#     def __call__(self, current_user: User = Depends(get_current_user)):
#
#         roles_as_strings = [role.name for role in current_user.roles]
#
#         if any(role in self.allowed_roles for role in roles_as_strings):
#             return True
#
#         raise InsufficientPermission()