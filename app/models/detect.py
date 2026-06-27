from pydantic import BaseModel

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
