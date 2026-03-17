from fastapi import FastAPI

from app.api.v1 import user
from app.api.v1.auth import auth_router
from app.core.config import config
from app.core.logging_config import setup_logging
from app.db.schema import Base
from app.db.database import engine
from app.exceptions.register import register_all_exceptions

setup_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=config.app_name,
    description=config.description,
    version=config.version
)

register_all_exceptions(app)

# Register routes
app.include_router(user.user_router, prefix=f"/api/v{config.version}", tags=["Users"])

app.include_router(auth_router, prefix=f"/api/v{config.version}", tags=["Auth"])