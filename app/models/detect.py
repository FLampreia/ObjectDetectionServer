import uuid
from datetime import datetime

from pydantic import BaseModel

from app.db.schema import DetectionType


class DownloadModelRequest(BaseModel):
    name: str


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: list[float]

class Area(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class FrameProcessingResponse(BaseModel):
    processing_time_per_frame: float
    detections_per_frame: list[Detection]


class VideoProcessingResponse(BaseModel):
    processing_time: float
    detections_per_frame: list[Detection]


class ListDetections(BaseModel):
    id: uuid.UUID
    username: str
    created_at: datetime
    model: str
    conf_threshold: float
    processing_time_ms: float
    count: int
    type: DetectionType


class ListObjects(BaseModel):
    id: uuid.UUID
    obj_name: str
    obj_class_id: int
    confidence: float