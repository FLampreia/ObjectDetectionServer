import uuid
from datetime import datetime

from pydantic import BaseModel
from pydantic import Field, model_validator
from typing import Literal

from app.db.schema import DetectionType


class DownloadModelRequest(BaseModel):
    name: str


class Detection(BaseModel):
    track_id: int | None = None
    class_id: int
    class_name: str
    confidence: float
    mean_confidence: float | None = Field(default=None, ge=0, le=1)
    confidence_samples: int | None = Field(default=None, ge=1)
    bbox: list[int] = Field(min_length=4, max_length=4)

class Area(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class Line(Area):
    @model_validator(mode="after")
    def validate_endpoints(self):
        if (self.x1, self.y1) == (self.x2, self.y2):
            raise ValueError("Counting line must have two different endpoints")
        return self


class CrossingEvent(Detection):
    track_id: int
    direction: Literal["A_to_B", "B_to_A"]

class FrameProcessingResponse(BaseModel):
    processing_time_per_frame: float = Field(ge=0)
    detections_per_frame: list[Detection]
    crossings: list[CrossingEvent] = Field(default_factory=list)


class SocketParameters(BaseModel):
    algorithm: str = Field(min_length=1)
    conf_threshold: float = Field(ge=0, le=1)
    detection_type: Literal["video", "stream"]
    chosen_team_id: uuid.UUID | None = None
    chosen_class_id: list[int] | None = None
    area: Area | None = None
    line: Line | None = None


class FrameMetadata(BaseModel):
    type: Literal["frame"] = "frame"
    frame_number: int = Field(ge=1)
    timestamp_ms: float = Field(ge=0, allow_inf_nan=False)


class StoredFrame(BaseModel):
    frame_number: int = Field(ge=1)
    timestamp_ms: float = Field(ge=0)
    image_public_id: str
    image_url: str
    detections: list[Detection] = Field(default_factory=list)
    crossings: list[CrossingEvent] = Field(default_factory=list)


class VideoProcessingResponse(BaseModel):
    processing_time: float = Field(ge=0, allow_inf_nan=False)
    inference_time_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    detections_per_frame: list[Detection]
    frames: list[StoredFrame] = Field(default_factory=list)


class ListDetections(BaseModel):
    id: uuid.UUID
    username: str
    created_at: datetime
    model: str
    conf_threshold: float
    processing_time_ms: float
    count: int
    type: DetectionType
    team_id: uuid.UUID | None = None
    team_name: str | None = None


class ListObjects(BaseModel):
    id: uuid.UUID
    obj_name: str
    obj_class_id: int
    confidence: float
    frame_confidence: float | None = None
    mean_confidence: float | None = None
    confidence_samples: int | None = None
    bbox: Area
    track_id: int | None = None
    image_id: uuid.UUID | None = None
    frame_number: int | None = None


class ListImages(BaseModel):
    id: uuid.UUID
    frame_number: int | None
    timestamp_ms: float | None
    image_url: str
    area: Area | None = None
    line: Line | None = None
    objects: list[ListObjects]
    crossings: list["ListCrossing"] = Field(default_factory=list)


class ListCrossing(BaseModel):
    id: uuid.UUID
    object_id: uuid.UUID
    image_id: uuid.UUID
    track_id: int
    obj_name: str
    obj_class_id: int
    direction: Literal["A_to_B", "B_to_A"]
    confidence: float
    frame_number: int
    timestamp_ms: float
    bbox: Area
