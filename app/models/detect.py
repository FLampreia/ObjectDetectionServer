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
