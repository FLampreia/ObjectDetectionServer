import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.middleware.cors import CORSMiddleware

from app.api.v1 import user
from app.api.v1.auth import auth_router
from app.core.config import config
from app.core.logging_config import setup_logging
from app.core.redis_config import check_redis_connection
from app.db.schema import Base
from app.db.database import engine
from app.exceptions.register import register_all_exceptions

setup_logging()
logger = logging.getLogger(__name__)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def life_span(app: FastAPI):
    logger.debug("Server is starting...")
    await check_redis_connection()
    yield
    logger.debug("Server as been stopped...")


app = FastAPI(
    title=config.app_name,
    description=config.description,
    version=config.version,
    lifespan=life_span
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_all_exceptions(app)

# Register routes
app.include_router(user.user_router, prefix=f"/api/v{config.version}", tags=["Users"])

app.include_router(auth_router, prefix=f"/api/v{config.version}", tags=["Auth"])