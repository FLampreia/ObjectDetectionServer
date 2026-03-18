from fastapi import Request, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.core.redis_config import token_in_blocklist
from app.exceptions.custom_exceptions import (
    InvalidToken,
    RefreshTokenRequired,
    AccessTokenRequired,
    InsufficientPermission
)
from app.db.schema import User
from app.db.database import get_db
from app.services.user_service import UserService
from security import decode_token

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(session=db)

class TokenBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)


    async def __call__(
            self,
            request: Request | None = None,
            websocket: WebSocket | None = None
    ) -> dict:

        creds: HTTPAuthorizationCredentials = await super().__call__(request)

        token = creds.credentials
        token_data = decode_token(token)

        if token_data is None:
            raise InvalidToken()

        if await token_in_blocklist(token_data["jti"]):
            raise InvalidToken()

        self.verify_token_data(token_data)

        return token_data

    def verify_token_data(self, token_data):
        raise NotImplementedError("Please override this method in child classes")

class AccessTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict) -> None:
        if token_data.get("refresh"):
            raise AccessTokenRequired()


class RefreshTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict) -> None:
        if not token_data.get("refresh"):
            raise RefreshTokenRequired()


def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    session: Session = Depends(get_db)
) -> User:

    user_email = token_details["user"]["email"]
    user_service = UserService(session)
    user = user_service.get_user_by_email(user_email)

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