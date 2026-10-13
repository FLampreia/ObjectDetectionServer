from fastapi import Request, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials


from app.core.deps import get_user_service
from app.services.redis_service import token_in_blocklist, is_session_revoked
from app.exceptions.custom_exceptions import (
    InvalidToken,
    RefreshTokenRequired,
    AccessTokenRequired,
    InsufficientPermission
)
from uuid import UUID
from app.db.schema import User
from app.services.user_service import UserService
from app.core.security import decode_token

# TODO: Review JTI and Redis handling and consider a dedicated token service.
class TokenBearer(HTTPBearer):
    check_blocklist = True

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

        self.verify_token_data(token_data)

        if self.check_blocklist and await token_in_blocklist(jti):
            raise InvalidToken()

        if await is_session_revoked(session_id):
            raise InvalidToken()

        return token_data

    def verify_token_data(self, token_data):
        raise NotImplementedError("Please override this method in child classes")

class AccessTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict) -> None:
        if token_data.get("type") != "access":
            raise AccessTokenRequired()


class RefreshTokenBearer(TokenBearer):
    # The refresh endpoint handles consumption and reuse in one Redis operation.
    check_blocklist = False

    def verify_token_data(self, token_data: dict) -> None:
        if token_data.get("type") != "refresh":
            raise RefreshTokenRequired()


class LogoutTokenBearer(TokenBearer):
    # A token already consumed by rotation can still identify the session to revoke.
    check_blocklist = False

    def verify_token_data(self, token_data: dict) -> None:
        if token_data.get("type") not in ("access", "refresh"):
            raise InvalidToken()


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


# TODO: Review role-based access to endpoints.
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
