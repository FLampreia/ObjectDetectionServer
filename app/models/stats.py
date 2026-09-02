from pydantic import BaseModel

from app.db.schema import DetectionType
from app.models.detect import ListDetections


class DetectionTypeUsage(BaseModel):
    type: DetectionType
    count: int


class TopObject(BaseModel):
    name: str
    count: int


class ModelsUsage(BaseModel):
    name: str
    count: int


class Stats(BaseModel):
    total_detections: int
    total_objects: int

    top_objects: list[TopObject]
    top_models: list[ModelsUsage]
    detection_types: list[DetectionTypeUsage]

    last_detections: list[ListDetections]
