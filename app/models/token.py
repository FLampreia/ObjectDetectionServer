from pydantic import BaseModel


class TokenResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str