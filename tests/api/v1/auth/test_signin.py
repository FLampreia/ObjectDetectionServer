import pytest

from tests.api.conftest import URL


def test_create_user_success(client, first_user_payload):
    response = client.post(f"{URL}/signin", json=first_user_payload)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == first_user_payload["email"]
    assert data["username"] == first_user_payload["username"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"username": "differentUsername"},  # same email
        {"email": "different@email.com"},  # same username
        {}  # same username + same email
    ],
    ids=[
        "existing_email",
        "existing_username",
        "duplicate_user"
    ]
)
def test_create_user_conflicts(
        client,
        first_user_payload,
        overrides
):
    response = client.post("/api/v1/signin", json=first_user_payload)
    assert response.status_code == 201

    duplicated_payload = {
        **first_user_payload,
        **overrides,
    }

    response = client.post(f"{URL}/signin", json=duplicated_payload)

    assert response.status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": None},
        {"password": None},
        {"password": "123"},

    ],
    ids=[
        "missing_email",
        "missing_password",
        "short_password"
    ]
)
def test_create_user_invalid_fields(
        client,
        first_user_payload,
        overrides
):
    invalid_payload = {
        **first_user_payload,
        **overrides
    }

    response = client.post(f"{URL}/signin", json=invalid_payload)
    assert response.status_code == 422
