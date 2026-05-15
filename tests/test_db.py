from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker


# Set up the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)