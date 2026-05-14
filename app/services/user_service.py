from sqlite3 import IntegrityError
from uuid import UUID
from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.security import generate_password_hash, verify_password
from app.db.schema import User
from app.exceptions.custom_exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
    DatabaseIntegrityException,
    EmailNotFound,
    InvalidCredentials, InvalidCurrentPassword, UserNotFound, NoFieldsToUpdate
)


class UserService:
    def __init__(self, session: Session):
        self._db = session

    def list_users(self) -> list[type[User]]:
        return self._db.query(User).all()

    def get_user(self, user_id: UUID) -> User | None:
        return self._db.query(User).filter(User.id == user_id).first()

    def create_user(self, username: str, password: str, email: EmailStr, full_name: str) -> User:
        user = User(
            username=username,
            password=generate_password_hash(password),
            email=email,
            full_name=full_name
        )

        self._db.add(user)

        try:
            self._db.commit()
            self._db.refresh(user)

            return user

        # In case data already exists
        except Exception as e:
            self._db.rollback()
            error_message = str(e)

            if "users.email" in error_message:
                raise EmailAlreadyExists()
            if "users.username" in error_message:
                raise UsernameAlreadyExists()

            raise DatabaseIntegrityException()

    def update_user_partial(self, user_id: UUID, username: str | None, password: str | None, full_name: str | None,
                            current_password: str | None) -> User | None:

        user = self.get_user(user_id)

        if not user:
            raise UserNotFound()

        if all(field is None for field in [username, password, full_name]):
            raise NoFieldsToUpdate()

        if username is not None:

            existing_user = (
                self._db.query(User)
                .filter(User.username == username)
                .first()
            )

            if existing_user and existing_user.id != user.id:
                raise UsernameAlreadyExists()

            user.username = username

        if full_name is not None:
            user.full_name = full_name

        if password is not None:
            if current_password is None:
                raise InvalidCurrentPassword()

            if not verify_password(current_password, user.password):
                raise InvalidCurrentPassword()

            user.password = generate_password_hash(password)

        self._db.commit()
        self._db.refresh(user)

        return user

    def delete_user(self, user_id: UUID) -> bool:
        user = self.get_user(user_id)
        if not user:
            raise UserNotFound()
        self._db.delete(user)
        self._db.commit()
        return True

    def get_user_by_email(self, user_email: EmailStr) -> User | None:

        user = self._db.query(User).filter(User.email == user_email).first()

        return user

    def verify_login(self, email: EmailStr, password: str) -> bool:
        user = self.get_user_by_email(email)

        if not user:
            return False

        return verify_password(password, str(user.password))
