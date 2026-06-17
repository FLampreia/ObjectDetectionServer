import enum
import uuid
from datetime import datetime
from typing import List

from pydantic import EmailStr
from sqlalchemy import String, create_engine, DateTime, Column, Enum, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )
    username: Mapped[str] = mapped_column(String, index=True, unique=True)
    password: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[EmailStr] = mapped_column(String, index=True, unique=True)
    full_name: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

    team_memberships: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}, created_at={self.created_at}, email={self.email}>"

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )

class TeamRole(enum.Enum):
    Owner = "owner"
    Member = "member"

class TeamMember(Base):
    __tablename__ = "team_members"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id"),
        primary_key=True
    )

    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole),
        default=TeamRole.Member
    )

    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="team_memberships"
    )

    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="members"
    )