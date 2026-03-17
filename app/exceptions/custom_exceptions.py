from app.exceptions.base import AppException


class EmailAlreadyExists(AppException):
    def __init__(self):
        super().__init__("Email already registered")

class UsernameAlreadyExists(AppException):
    def __init__(self):
        super().__init__("Username already registered")

class DatabaseIntegrityException(AppException):
    def __init__(self):
        super().__init__("Database integrity exception")

class EmailNotFound(AppException):
    def __init__(self):
        super().__init__("Email not found")

class UserNotFound(AppException):
    def __init__(self):
        super().__init__("User not found")

class InvalidToken(AppException):
    def __init__(self):
        super().__init__("Invalid token")

class RevokedToken(AppException):
    def __init__(self):
        super().__init__("Revoked token")

class RefreshTokenRequired(AppException):
    def __init__(self):
        super().__init__("Refresh token required")

class AccessTokenRequired(AppException):
    def __init__(self):
        super().__init__("Access token required")

class InsufficientPermission(AppException):
    def __init__(self):
        super().__init__("Insufficient permission")

class InvalidCredentials(AppException):
    def __init__(self):
        super().__init__("Invalid credentials")