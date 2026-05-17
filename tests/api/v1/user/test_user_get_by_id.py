import uuid

import pytest

from tests.api.conftest import URL


def test_get_user_by_id_success(
        client,
        first_user_payload,
        auth_headers_factory,
        current_user
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user(user1_headers)

    response = client.get(f"{URL}/users/{user1["id"]}", headers=user1_headers)
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user1["id"])
    assert data["username"] == user1["username"]
    assert data["email"] == user1["email"]
    assert data["full_name"] == user1["full_name"]


def test_get_user_by_id_not_found(
        client,
        first_user_payload,
        auth_headers_factory,
):
    user1_headers = auth_headers_factory(first_user_payload)
    user_id = uuid.uuid4()

    response = client.get(
        f"{URL}/users/{user_id}",
        headers=user1_headers
    )

    assert response.status_code == 404


def test_get_user_by_id_requires_auth(
        client
):
    response = client.get(f"{URL}/users/{uuid.uuid4()}")
    assert response.status_code == 401

def test_get_user_by_id_invalid_uuid(
        client,
        first_user_payload,
        auth_headers_factory,
):
    user1_headers = auth_headers_factory(first_user_payload)

    response = client.get(
        f"{URL}/users/INVALIDUUID",
        headers=user1_headers
    )

    assert response.status_code == 422
