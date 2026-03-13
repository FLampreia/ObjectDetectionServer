from sqlite3 import IntegrityError
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.schema import User
from app.exceptions.user_exceptions import EmailAlreadyExists, UsernameAlreadyExists, DatabaseIntegrityException


class UserService:
    def __init__(self, session: Session):
        self._db = session

    def list_users(self) -> list[type[User]]:
        return self._db.query(User).all()

    def get_user(self, user_id: UUID) -> User | None:
        return self._db.query(User).filter(User.id == user_id).first()

    def create_user(self, username: str, password: str, email: str, full_name: str) -> User:
        user = User(
            username=username,
            password=password,
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

    def update_user(self, user_id: UUID, username: str, password: str, email: str, full_name: str) -> User | None:
        user = self.get_user(user_id)
        if not user:
            return None
        user.username = username
        user.password = password
        user.email = email
        user.full_name = full_name
        self._db.commit()
        self._db.refresh(user)
        return user

    def delete_user(self, user_id: UUID) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        self._db.delete(user)
        self._db.commit()
        return True