import enum
import uuid
from datetime import datetime
from typing import List

from pydantic import EmailStr
from sqlalchemy import String, create_engine, DateTime, Column, Enum, ForeignKey, Boolean, Float, Integer, UniqueConstraint
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

class DetectionType(enum.Enum):
    Photo = "photo"
    Video = "video"
    Stream = "stream"

class Detection(Base):
    __tablename__ = "detection"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id"),
        index=True,
        nullable=True
    )

    model: Mapped["str"] = mapped_column(String, index=True)
    conf_threshold: Mapped["float"] = mapped_column(Float)
    processing_time_ms: Mapped["float"] = mapped_column(Float)
    inference_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    type: Mapped[DetectionType] = mapped_column(
        Enum(DetectionType)
    )

    area_x1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_y1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_x2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_y2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_x1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_y1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_x2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_y2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crossings: Mapped[list["LineCrossing"]] = relationship(
        "LineCrossing", back_populates="detection", cascade="all, delete-orphan",
    )

    user: Mapped["User"] = relationship("User")
    team: Mapped["Team"] = relationship("Team")

    objects: Mapped[list["DetectedObject"]] = relationship(
        "DetectedObject",
        back_populates="detection",
        cascade="all, delete-orphan"
    )
    images: Mapped[list["DetectionImage"]] = relationship(
        "DetectionImage", back_populates="detection",
        cascade="all, delete-orphan", order_by="DetectionImage.frame_number",
    )


class DetectionImage(Base):
    __tablename__ = "detection_image"
    __table_args__ = (UniqueConstraint("detection_id", "frame_number"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    detection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("detection.id", ondelete="CASCADE"), index=True,
    )
    frame_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_public_id: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str] = mapped_column(String)
    detection: Mapped["Detection"] = relationship("Detection", back_populates="images")
    objects: Mapped[list["DetectedObject"]] = relationship(
        "DetectedObject", back_populates="image", cascade="all, delete-orphan",
        order_by="DetectedObject.track_id",
    )
    crossings: Mapped[list["LineCrossing"]] = relationship(
        "LineCrossing", back_populates="image", cascade="all, delete-orphan",
    )


class LineCrossing(Base):
    __tablename__ = "line_crossing"
    __table_args__ = (UniqueConstraint("detection_id", "frame_number", "track_id"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    detection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("detection.id", ondelete="CASCADE"), index=True)
    image_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("detection_image.id", ondelete="CASCADE"), index=True)
    object_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("detected_object.id", ondelete="CASCADE"), index=True)
    track_id: Mapped[int] = mapped_column(Integer)
    direction: Mapped[str] = mapped_column(String)
    frame_number: Mapped[int] = mapped_column(Integer)
    timestamp_ms: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    bbox_x1: Mapped[int] = mapped_column(Integer)
    bbox_y1: Mapped[int] = mapped_column(Integer)
    bbox_x2: Mapped[int] = mapped_column(Integer)
    bbox_y2: Mapped[int] = mapped_column(Integer)
    detection: Mapped["Detection"] = relationship("Detection", back_populates="crossings")
    image: Mapped["DetectionImage"] = relationship("DetectionImage", back_populates="crossings")
    object: Mapped["DetectedObject"] = relationship("DetectedObject")

class DetectedObject(Base):
    __tablename__ = "detected_object"
    __table_args__ = (UniqueConstraint("detection_id", "track_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    detection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("detection.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    object_name: Mapped[str] = mapped_column(String, index=True)
    object_class_id: Mapped[int] = mapped_column(Integer, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    mean_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("detection_image.id"), nullable=True, index=True,
    )
    image: Mapped["DetectionImage | None"] = relationship("DetectionImage", back_populates="objects")

    bbox_x1: Mapped[int | None] = mapped_column(Integer, nullable=False)
    bbox_y1: Mapped[int | None] = mapped_column(Integer, nullable=False)
    bbox_x2: Mapped[int | None] = mapped_column(Integer, nullable=False)
    bbox_y2: Mapped[int | None] = mapped_column(Integer, nullable=False)

    detection: Mapped["Detection"] = relationship(
        "Detection",
        back_populates="objects"
    )
