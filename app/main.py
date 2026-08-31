import logging
import httpx
from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.middleware.cors import CORSMiddleware


from app.api.v1.auth import auth_router
from app.api.v1.detect import detect_router
from app.api.v1.detections import detections_router
from app.api.v1.models import models_router
from app.api.v1.socket import socket_router
from app.api.v1.team import team_router
from app.api.v1.user import user_router
from app.core.config import config
from app.core.logging_config import setup_logging
from app.core.redis_config import check_redis_connection
from app.db.schema import Base
from app.db.database import engine as default_engine
from app.exceptions.register import register_all_exceptions

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def life_span(app: FastAPI):
    logger.debug("Server is starting...")

    await check_redis_connection()

    yield

    logger.debug("Server as been stopped...")

def create_app(engine = None, with_lifespan: bool = True) -> FastAPI:

    if engine is None:
        engine = default_engine

    # Create database tables
    Base.metadata.create_all(bind=engine)

    lifespan = life_span if with_lifespan else None

    fastapi_app: FastAPI = FastAPI(
        title=config.app_name,
        description=config.description,
        version=config.version,
        lifespan=lifespan
    )

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://192.168.1.66:3000",  # pc casa mae
            "http://192.168.1.145:3000"  # pc casa leonor
        ],
        # allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_all_exceptions(fastapi_app)

    # Register routes
    fastapi_app.include_router(
        user_router,
        prefix=f"/api/v{config.version}",
        tags=["Users"]
    )

    fastapi_app.include_router(
        auth_router,
        prefix=f"/api/v{config.version}",
        tags=["Auth"]
    )

    fastapi_app.include_router(
        team_router,
        prefix=f"/api/v{config.version}",
        tags=["Teams"]
    )

    fastapi_app.include_router(
        detect_router,
        prefix=f"/api/v{config.version}",
        tags=["Detect"]
    )

    fastapi_app.include_router(
        socket_router,
        prefix=f"/api/v{config.version}",
        tags=["Socket"]
    )

    fastapi_app.include_router(
        models_router,
        prefix=f"/api/v{config.version}",
        tags=["Models"]
    )

    fastapi_app.include_router(
        detections_router,
        prefix=f"/api/v{config.version}",
        tags=["Detections"]
    )

    return fastapi_app


