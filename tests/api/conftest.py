from unittest.mock import MagicMock

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from app.core.deps import get_user_service
from app.main import create_app
from app.db.database import get_db

URL = f"/api/v1"

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


# -------------------------------------------------
# DATABASE (tests isolation)
# -------------------------------------------------
# @pytest.fixture(scope="session", autouse=True)
# def setup_database():
#     Base.metadata.create_all(bind=test_engine)
#     yield
#     Base.metadata.drop_all(bind=test_engine)
#

@pytest.fixture(scope="function")
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()

    db = TestingSessionLocal(bind=connection)

    try:
        yield db
    finally:
        db.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()


# -------------------------------------------------
# APP + CLIENT
# -------------------------------------------------
@pytest.fixture(scope="function")
def app(db_session):

    app = create_app(engine=test_engine , with_lifespan=False)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    yield app

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app):
    return TestClient(app)


# -------------------------------------------------
# USER FIXTURE
# -------------------------------------------------
@pytest.fixture
def user_payload():
    unique = str(uuid.uuid4())[:8]

    return {
        "username": f"user_{unique}",
        "email": f"user_{unique}@test.com",
        "password": "password123",
        "full_name": "Test User"
    }


# Create user through API
@pytest.fixture
def create_user(client, user_payload):
    response = client.post(f"{URL}/signin", json=user_payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def current_user(client, auth_headers):
    response = client.get(f"{URL}/me", headers=auth_headers)
    return response.json()


# -------------------------------------------------
# AUTH FLOW (authenticate suer)
# -------------------------------------------------
# todo verificar se vale a pena ter auth_token e auth_headers quando tenho authenticated_user
@pytest.fixture
def auth_token(client, create_user, user_payload):
    response = client.post(f"{URL}/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })

    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def authenticated_user(client, user_payload):
    client.post("/api/v1/signin", json=user_payload)

    response = client.post(
        "/api/v1/login",
        json={
            "email": user_payload["email"],
            "password": user_payload["password"]
        }
    )

    data = response.json()

    return {
        "user": user_payload,
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "access_headers": {
            "Authorization": f"Bearer {data['access_token']}"
        },
        "refresh_headers": {
            "Authorization": f"Bearer {data['refresh_token']}"
        }
    }


# -------------------------------------------------
# FULL LOGIN (return tokens)
# -------------------------------------------------
@pytest.fixture
def login_data(client, user_payload):
    client.post(f"{URL}/signin", json=user_payload)

    response = client.post(f"{URL}/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })

    return response.json()


# -------------------------------------------------
# MOCKS
# -------------------------------------------------
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


@pytest.fixture
def mock_user_service(client):
    service = MagicMock()
    client.app.dependency_overrides[get_user_service] = lambda: service
    yield service
    client.app.dependency_overrides.clear()


# -------------------------------------------------
# TEAM
# -------------------------------------------------
@pytest.fixture
def team_payload():
    unique = str(uuid.uuid4())[:8]

    return {
        "name": f"team_{unique}"
    }


@pytest.fixture
def created_team(client, auth_headers, team_payload):
    response = client.post(
        f"{URL}/team",
        headers=auth_headers,
        json=team_payload
    )
    assert response.status_code == 201

    return response.json()


# -------------------------------------------------
# SECOND USER
# -------------------------------------------------
@pytest.fixture
def second_user_payload():
    unique = str(uuid.uuid4())[:8]

    return {
        "username": f"second_user_{unique}",
        "email": f"second_user_{unique}@test.com",
        "password": "password123",
        "full_name": "Second User"
    }


@pytest.fixture
def create_second_user(client, second_user_payload):
    response = client.post(
        f"{URL}/signin",
        json=second_user_payload
    )

    assert response.status_code == 201

    return response.json()


@pytest.fixture
def auth_headers_second_user(client, create_second_user, second_user_payload):
    response = client.post(
        f"{URL}/login",
        json={
            "email": second_user_payload["email"],
            "password": second_user_payload["password"]
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }