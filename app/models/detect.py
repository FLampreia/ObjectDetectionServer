from pydantic import BaseModel

class DownloadModelRequest(BaseModel):
    name: str