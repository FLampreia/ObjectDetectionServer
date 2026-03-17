from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import config

# Create the connection with database
engine = create_engine(
    config.db_url,
    connect_args={
        "check_same_thread": False
    }
)

# Transaction handler with database
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create a session each time there is a request, and closes it when its finished
def get_db() -> Generator[Session, None, None]:

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()