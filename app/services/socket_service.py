import json
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from fastapi import WebSocket
from starlette.concurrency import run_in_threadpool

from app.db.database import SessionLocal
from app.db.schema import DetectionType, TeamMember, User
from app.models.detect import FrameProcessingResponse, SocketParameters, VideoProcessingResponse, FrameMetadata, StoredFrame
from app.services.processor_service import DetectService
from app.services.cloudinary_service import upload_frame_image, delete_image

logger = logging.getLogger(__name__)
MAX_PENDING_UPLOADS = 4
UPLOAD_CONCURRENCY = 2


@dataclass
class PendingFrame:
    metadata: FrameMetadata
    content: bytes


@dataclass
class SocketContext:
    started_at: float = field(default_factory=time.perf_counter)
    pending: PendingFrame | None = None
    last_frame_number: int = 0
    seen_tracks: set[int] = field(default_factory=set)
    frames: list[StoredFrame] = field(default_factory=list)
    uploaded_ids: list[str] = field(default_factory=list)
    committed: bool = False
    upload_tasks: set[asyncio.Task] = field(default_factory=set)
    upload_slots: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(UPLOAD_CONCURRENCY))
    upload_failed: asyncio.Event = field(default_factory=asyncio.Event)
    upload_error: Exception | None = None

    def new_objects(self, response, area=None):
        new = []
        for detection in response.detections_per_frame:
            if detection.track_id is None or detection.track_id in self.seen_tracks:
                continue
            self.seen_tracks.add(detection.track_id)
            obj = detection.model_copy(deep=True)
            if area is not None:
                left, top = min(area.x1, area.x2), min(area.y1, area.y2)
                obj.bbox = [obj.bbox[0] + left, obj.bbox[1] + top, obj.bbox[2] + left, obj.bbox[3] + top]
            new.append(obj)
        return new


class SocketService:
    @staticmethod
    def check_upload_error(context: SocketContext):
        if context.upload_error is not None:
            raise RuntimeError("Frame image upload failed") from context.upload_error

    async def watch_upload_failure(self, context: SocketContext):
        await context.upload_failed.wait()
        self.check_upload_error(context)

    async def upload_frame(self, pending: PendingFrame, new_objects, context: SocketContext):
        async with context.upload_slots:
            uploaded = await upload_frame_image(pending.content)
            context.uploaded_ids.append(uploaded["public_id"])
            context.frames.append(StoredFrame(
                frame_number=pending.metadata.frame_number,
                timestamp_ms=pending.metadata.timestamp_ms,
                image_public_id=uploaded["public_id"], image_url=uploaded["secure_url"],
                detections=new_objects,
            ))

    async def queue_upload(self, pending: PendingFrame, new_objects, context: SocketContext):
        self.check_upload_error(context)
        # Bound retained JPEGs; slow storage applies backpressure instead of growing memory.
        while len(context.upload_tasks) >= MAX_PENDING_UPLOADS:
            await asyncio.wait(context.upload_tasks, return_when=asyncio.FIRST_COMPLETED)
            self.check_upload_error(context)
        task = asyncio.create_task(self.upload_frame(pending, new_objects, context))
        context.upload_tasks.add(task)

        def completed(upload_task):
            context.upload_tasks.discard(upload_task)
            if upload_task.cancelled():
                error = RuntimeError("Frame image upload was cancelled")
            else:
                error = upload_task.exception()
            if error is not None and context.upload_error is None:
                context.upload_error = error
                context.upload_failed.set()

        task.add_done_callback(completed)

    async def wait_for_uploads(self, context: SocketContext):
        if context.upload_tasks:
            # Connection cancellation must not lose the IDs of successful uploads.
            await asyncio.shield(asyncio.gather(*context.upload_tasks, return_exceptions=True))

    @staticmethod
    def validate_membership(db, user_id, parameters):
        if db.get(User, user_id) is None:
            raise ValueError("User no longer exists")
        if parameters.chosen_team_id is not None:
            if db.get(TeamMember, (user_id, parameters.chosen_team_id)) is None:
                raise ValueError("User is not a member of the selected team")

    def validate_owner(self, user_id: UUID, parameters: SocketParameters):
        with SessionLocal() as db:
            self.validate_membership(db, user_id, parameters)

    def save_result(self, user_id, parameters, created_at, result, started_at):
        with SessionLocal() as db:
            self.validate_membership(db, user_id, parameters)
            return DetectService(db).add_video_detection_to_db(
                user_id=user_id,
                team_id=parameters.chosen_team_id,
                model=parameters.algorithm,
                conf_threshold=parameters.conf_threshold,
                created_at=created_at,
                detection_type=DetectionType(parameters.detection_type),
                result=result,
                area=parameters.area,
                started_at=started_at,
            )

    async def cleanup(self, context: SocketContext):
        await self.wait_for_uploads(context)
        if context.committed:
            return
        for public_id in context.uploaded_ids:
            try:
                await delete_image(public_id)
            except Exception:
                logger.exception("Could not delete abandoned frame image %s", public_id)

    async def forward_to_processor(self, frontend_ws: WebSocket, processor_ws, context: SocketContext):
        metadata = None
        while True:
            message = await frontend_ws.receive()
            if message["type"] == "websocket.disconnect":
                return
            if message.get("text") is not None:
                command = json.loads(message["text"])
                if metadata is not None:
                    raise ValueError("Expected frame bytes")
                if command.get("type") == "frame":
                    metadata = FrameMetadata.model_validate(command)
                    if context.pending is not None or metadata.frame_number <= context.last_frame_number:
                        raise ValueError("Frames must be sent in order, awaiting each response")
                elif command.get("type") != "finish":
                    raise ValueError("Expected frame or finish")
                await processor_ws.send(message["text"])
            elif message.get("bytes") is not None:
                if metadata is None:
                    raise ValueError("Frame metadata is missing")
                if len(message["bytes"]) > 8 * 1024 * 1024:
                    raise ValueError("Frame exceeds 8 MiB")
                context.pending = PendingFrame(metadata, message["bytes"])
                context.last_frame_number = metadata.frame_number
                metadata = None
                await processor_ws.send(message["bytes"])

    async def forward_to_frontend(
        self, frontend_ws: WebSocket, processor_ws, user_id: UUID,
        parameters: SocketParameters, created_at: datetime, context: SocketContext,
    ):
        inference_time_ms = 0.0
        async for message in processor_ws:
            if not isinstance(message, str):
                await frontend_ws.send_bytes(message)
                continue
            payload = json.loads(message)
            if payload.get("status") == "error":
                await frontend_ws.send_text(message)
                raise ValueError("Worker rejected processing")
            if payload.get("status") == "finished":
                if context.pending is not None:
                    raise ValueError("Worker finished with an unanswered frame")
                await self.wait_for_uploads(context)
                self.check_upload_error(context)
                context.frames.sort(key=lambda frame: frame.frame_number)
                result = VideoProcessingResponse(
                    processing_time=(time.perf_counter() - context.started_at) * 1000,
                    inference_time_ms=inference_time_ms,
                    detections_per_frame=[obj for frame in context.frames for obj in frame.detections],
                    frames=context.frames,
                )
                save_task = asyncio.create_task(run_in_threadpool(
                    self.save_result, user_id, parameters, created_at, result, context.started_at,
                ))
                try:
                    processing_time_ms = await asyncio.shield(save_task)
                except asyncio.CancelledError:
                    # Wait for the commit outcome before deciding whether images are orphaned.
                    await save_task
                    context.committed = True
                    raise
                context.committed = True
                await frontend_ws.send_json({
                    "status": "finished", "saved": True,
                    "processing_time_ms": processing_time_ms,
                    "inference_time_ms": inference_time_ms,
                })
                return
            frame = FrameProcessingResponse.model_validate(payload)
            pending = context.pending
            if pending is None or payload.get("frame_number") != pending.metadata.frame_number:
                raise ValueError("Worker frame response does not match the submitted image")
            context.pending = None
            inference_time_ms += frame.processing_time_per_frame
            new_objects = context.new_objects(frame, parameters.area)
            self.check_upload_error(context)
            if new_objects:
                await self.queue_upload(pending, new_objects, context)
            # Keep crop-relative coordinates for the existing frontend drawing.
            await frontend_ws.send_text(message)
        raise RuntimeError("Worker closed before confirming completion")
