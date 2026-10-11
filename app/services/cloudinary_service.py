from uuid import uuid4
from io import BytesIO

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.config import config


cloudinary.config(
    cloud_name=config.CLOUDINARY_CLOUD_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True,
)


async def upload_image(image: UploadFile) -> dict:
    await image.seek(0)

    try:
        return await run_in_threadpool(
            cloudinary.uploader.upload,
            image.file,
            resource_type="image",
            public_id=f"object-detection/images/{uuid4().hex}",
            overwrite=False,
            timeout=30,
        )
    finally:
        await image.seek(0)

async def delete_image(public_id: str):

        return await run_in_threadpool(cloudinary.uploader.destroy, public_id)


async def upload_frame_image(content: bytes) -> dict:
    return await run_in_threadpool(
        cloudinary.uploader.upload,
        BytesIO(content),
        resource_type="image",
        public_id=f"object-detection/frames/{uuid4().hex}",
        overwrite=False,
        timeout=30,
    )
