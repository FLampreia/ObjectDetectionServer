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


class InvalidSession(AppException):
    def __init__(self):
        super().__init__("Invalid session")


class MalformedToken(AppException):
    def __init__(self):
        super().__init__("Malformed token")


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


class RedisNotAvailable(AppException):
    def __init__(self):
        super().__init__("Redis not available")


class InvalidCurrentPassword(AppException):
    def __init__(self):
        super().__init__("Invalid current password")


class UserAlreadyInTeam(AppException):
    def __init__(self):
        super().__init__("User already exists")


class NotTeamOwner(AppException):
    def __init__(self):
        super().__init__("Not a team owner")


class NotAllowedToRemoveOwner(AppException):
    def __init__(self):
        super().__init__("Cannot remove owner")


class NotAllowedToUpdate(AppException):
    def __init__(self):
        super().__init__("Not allowed to update")


class NotAllowedToDelete(AppException):
    def __init__(self):
        super().__init__("Not allowed to delete")


class NoFieldsToUpdate(AppException):
    def __init__(self):
        super().__init__("At least one field must be provided for update")


class TeamNameAlreadyExists(AppException):
    def __init__(self):
        super().__init__("Team name already exists")


class TeamNotFound(AppException):
    def __init__(self):
        super().__init__("Team not found")


class DetectionNotFound(AppException):
    def __init__(self):
        super().__init__("Detection not found")


class FailedUploadingToCloud(AppException):
    def __init__(self):
        super().__init__("It was not possible to upload the file to the cloud.")


class FailedDeletingFromCloud(AppException):
    def __init__(self):
        super().__init__("It was not possible to delete the file from the cloud.")
