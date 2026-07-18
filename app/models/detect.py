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


class DetectionResponse(BaseModel):
    filename: str
    size_x: int
    size_y: int
    processing_time_ms: float
    detections: list[Detection]

class ListDetections(BaseModel):
    id: uuid.UUID
    username: str
    created_at: datetime
    model: str
    conf_threshold: float
    processing_time_ms: float
    count: int
    type: DetectionType
