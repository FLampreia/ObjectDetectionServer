import enum
import uuid
from datetime import datetime

from sqlalchemy import String, create_engine, DateTime, Column, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass

class Role(enum.Enum):
    Viewer = "viewer"
    Operator = "operator"
    Admin = "admin"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )
    username: Mapped[str] = mapped_column(String, index=True, unique=True)
    password: Mapped[str] = mapped_column(String, index=True) #TODO encriptar a password
    email: Mapped[str] = mapped_column(String, index=True, unique=True)
    full_name: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role), index=True, default=Role.Viewer)

    def __repr__(self):
        return f"<User {self.username}, created_at={self.created_at}, email={self.email}>"

