import logging
import asyncio
from contextlib import suppress
from datetime import datetime
from uuid import UUID, uuid4
from starlette.concurrency import run_in_threadpool
from starlette.websockets import WebSocketState
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app.core.config import config
from app.services.redis_service import register_socket_session, consume_socket_session

from app.core.deps import get_socket_service
from app.models.detect import SocketParameters
from app.services.socket_service import SocketService, SocketContext
from app.core.token import get_current_user

socket_router = APIRouter()
logger = logging.getLogger(__name__)


@socket_router.post("/socket/session")
async def get_socket_connection_to_worker(
        current_user=Depends(get_current_user)
):
    session_id = str(uuid4())
    try:
        await register_socket_session(
            session_id=session_id,
            user_id=str(current_user.id)
        )

        logger.info("Backend WebSocket session created")

        return session_id

    except Exception as e:
        logger.exception("Failed to register backend WebSocket session")
        raise HTTPException(503, "Session service unavailable") from e

@socket_router.websocket("/socket/connect/{session_id}")
async def connect_socket(
    websocket: WebSocket,
    session_id: str,
    socket_service: SocketService = Depends(get_socket_service)
):
    tasks = []
    close_code = 1000
    context = SocketContext()

    try:
        try:
            UUID(session_id)
        except ValueError:
            await websocket.close(code=1008)
            return
        user_id = await consume_socket_session(session_id)

        if user_id is None:
            await websocket.close(code=1008)
            return

        processor_url= (
            f"ws://{config.PROCESSOR_HOST}:"
            f"{config.PROCESSOR_PORT}"
            f"/detect/video/socket/connect"
        )

        async with connect(
                processor_url,
                proxy=None,
                open_timeout=10,
                max_size=8 * 1024 * 1024,
        ) as processor_ws:
            await websocket.accept()

            try:
                parameters = SocketParameters.model_validate(
                    await asyncio.wait_for(websocket.receive_json(), timeout=30)
                )
                await run_in_threadpool(socket_service.validate_owner, UUID(user_id), parameters)
            except ValueError as exc:
                await websocket.send_json({"status": "error", "detail": str(exc)})
                close_code = 1008
                return
            await processor_ws.send(parameters.model_dump_json())

            logger.info(
                "Processing WebSocket opened for user %s",
                user_id,
            )

            tasks = [
                asyncio.create_task(
                    socket_service.forward_to_processor(websocket, processor_ws, context)
                ),
                asyncio.create_task(
                    socket_service.forward_to_frontend(
                        websocket, processor_ws, UUID(user_id), parameters, datetime.now(), context,
                    )
                ),
            ]

            try:
                done, _ = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in done:
                    task.result()
            finally:
                for task in tasks:
                    task.cancel()

                await asyncio.gather(
                    *tasks,
                    return_exceptions=True,
                )

    except WebSocketDisconnect:
        pass
    except ConnectionClosed as exc:
        if exc.rcvd is None or exc.rcvd.code not in (1000, 1001):
            close_code = 1011
            logger.warning("Connection to processor interrupted")
    except Exception:
        close_code = 1011
        logger.exception("Error connecting to WebSocket")
        if websocket.application_state == WebSocketState.CONNECTED:
            with suppress(Exception):
                await websocket.send_json({"status": "error", "detail": "Processing or saving failed"})
    finally:
        if websocket.application_state != WebSocketState.DISCONNECTED:
            with suppress(RuntimeError, WebSocketDisconnect, OSError):
                await websocket.close(code=close_code)
        await socket_service.cleanup(context)
