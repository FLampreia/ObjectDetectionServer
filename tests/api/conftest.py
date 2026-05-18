import uuid

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.db.database import get_db
from app.db.schema import Base
from app.main import create_app

URL = f"/api/v1"

# Set up the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"

# -------------------------------------------------
# DATABASE
# -------------------------------------------------
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


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """
    Creates all database tables before the test session starts and drops them after it ends.

    This ensures a clean test database environment for the entire test suite.

    Yields:
        None
    """

    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Provides an isolated SQLAlchemy session for each test function.

    This fixture creates a new database connection and wraps it in a transaction,
    ensuring full test isolation. All changes made during the test are rolled back
    after execution, preventing side effects between tests.

    Yields:
        Session: SQLAlchemy testing session bound to a transactional connection.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# # -------------------------------------------------
# # APP + CLIENT
# # -------------------------------------------------
@pytest.fixture(scope="function")
def client(db_session):
    """
    Creates a FastAPI TestClient configured to use an in-memory test database.

    This fixture overrides the application's `get_db` dependency so that all
    database interactions during tests use the provided `db_session`.

    Args:
        db_session: SQLAlchemy session bound to the test database.

    Yields:
        TestClient: A FastAPI TestClient instance for making test requests.
    """

    app = create_app(engine=test_engine, with_lifespan=False)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# -------------------------------------------------
# USER
# -------------------------------------------------
#todo pensar em fazer factory como fiz em team e utilizar apenas um payload
@pytest.fixture
def first_user_payload():
    """
    Create a payload with unique data for user creation tests.

    Returns:
        dict: Dictionary containing the user registration data.
    """

    unique = str(uuid.uuid4())[:8]

    return {
        "username": f"user_{unique}",
        "email": f"user_{unique}@test.com",
        "password": "password123",
        "full_name": "Test User"
    }


@pytest.fixture
def second_user_payload():
    """
    Create a second user payload with unique data for testing purposes.

    Returns:
        dict: Dictionary containing registration data for a secondary test user.
    """

    uid = uuid.uuid4().hex[:8]

    return {
        "email": f"second_{uid}@test.com",
        "username": f"second_{uid}",
        "password": "password123",
        "full_name": "Second Test User"
    }


@pytest.fixture
def create_user_factory(client):
    """
    Factory fixture to create a user via the API.

    Returns a callable that receives a payload and creates a user,
    asserting that the operation succeeds.

    Returns:
        Callable[[dict], dict]: Function that creates a user and returns the response data.
    """

    def _create(payload):
        response = client.post(
            f"{URL}/signin",
            json=payload
        )

        assert response.status_code == 201
        return response.json()

    return _create


@pytest.fixture
def login_user(client, create_user_factory):
    """
    Factory fixture to create and authenticate a user.

    This first creates a user using the create_user fixture and then performs
    a login request using the provided credentials.

    Returns:
        Callable[[dict], dict]: Function that logs in a user and returns authentication data.
    """

    def _login(payload):
        create_user_factory(payload)

        response = client.post(
            f"{URL}/login",
            json={
                "email": payload["email"],
                "password": payload["password"]
            }
        )

        assert response.status_code == 200
        return response.json()

    return _login


@pytest.fixture
def current_user_factory(client):
    """
    Factory fixture to retrieve the currently authenticated user.

    This fixture returns a function that performs a request to the `/me`
    endpoint using provided authentication headers and returns the user data.

    Returns:
        Callable[[dict], dict]: Function that fetches the authenticated user information.
    """

    def _current(auth_headers):
        response = client.get(f"{URL}/me", headers=auth_headers)
        assert response.status_code == 200
        return response.json()

    return _current


# -------------------------------------------------
# Auth Headers
# -------------------------------------------------

@pytest.fixture
def auth_headers_factory(login_user):
    """
    Factory fixture to generate authentication headers for any user payload.

    Returns:
        Callable[[dict], dict]: Function that returns Authorization headers.
    """

    def _factory(user_payload):
        login_data = login_user(user_payload)

        return {
            "Authorization": f"Bearer {login_data['access_token']}"
        }

    return _factory


# -------------------------------------------------
# TEAM
# -------------------------------------------------
@pytest.fixture
def team_payload_factory():
    """
    Factory fixture that generates unique team payloads for testing.

    Each call produces a new payload with a unique team name to ensure
    test isolation and avoid name collisions.

    Returns:
        Callable[[], dict]: Function that returns a new team payload dictionary.
    """
    def _create():
        unique = str(uuid.uuid4())[:8]
        return {
            "name": f"team_{unique}"
        }

    return _create


@pytest.fixture
def created_team_factory(client, auth_headers_factory):
    """
    Factory fixture to create a team via the API.

    This fixture performs a team creation request using provided authentication
    headers and returns the created team data.

    Returns:
        Callable[[dict], dict]: Function that creates a team and returns the response data.
    """
    def _create(auth_header, team_payload):
        response = client.post(
            f"{URL}/team",
            headers=auth_header,
            json=team_payload
        )
        assert response.status_code == 201

        return response.json()

    return _create


# -------------------------------------------------
# MOCKS
# -------------------------------------------------
# todo ao criar o token service.py, rever este mock
@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    blocked_jtis = set()
    revoked_sessions = set()

    async def fake_token_in_blocklist(jti):
        return jti in blocked_jtis

    async def fake_add_jti(jti):
        blocked_jtis.add(jti)

    async def fake_is_session_revoked(session_id):
        return session_id in revoked_sessions

    async def fake_revoke_session(session_id):
        revoked_sessions.add(session_id)

    # token.py
    monkeypatch.setattr(
        "app.core.token.token_in_blocklist",
        fake_token_in_blocklist
    )

    monkeypatch.setattr(
        "app.core.token.is_session_revoked",
        fake_is_session_revoked
    )

    # auth.py
    monkeypatch.setattr(
        "app.api.v1.auth.token_in_blocklist",
        fake_token_in_blocklist
    )

    monkeypatch.setattr(
        "app.api.v1.auth.is_session_revoked",
        fake_is_session_revoked
    )

    monkeypatch.setattr(
        "app.api.v1.auth.add_jti_to_blocklist",
        fake_add_jti
    )

    monkeypatch.setattr(
        "app.api.v1.auth.revoke_session",
        fake_revoke_session
    )

#
# @pytest.fixture
# def mock_user_service(client):
#     service = MagicMock()
#     client.app.dependency_overrides[get_user_service] = lambda: service
#     yield service
#     client.app.dependency_overrides.clear()
#
#
