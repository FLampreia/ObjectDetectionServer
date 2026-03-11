from sqlalchemy.orm import Session

from app.db.schema import User

class UserService:
    def __init__(self, session: Session):
        self._db = session

    def list_users(self) -> list[type[User]]:
        return self._db.query(User).all()

    def get_user(self, user_id: int) -> User | None:
        return self._db.query(User).filter(User.id == user_id).first()

    def create_user(self, username: str, password: str, email: str, full_name: str) -> User:
        user = User(
            username=username,
            password=password,
            email=email,
            full_name=full_name
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user