import uuid

import pytest

from tests.api.conftest import URL


def test_get_user_by_id_success(client, auth_headers, db_user):
    response = client.get(f"{URL}/users/{db_user.id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(db_user.id)
    assert data["username"] == db_user.username
    assert data["email"] == db_user.email
    assert data["full_name"] == db_user.full_name


def test_get_user_by_id_not_found(client, auth_headers):
    user_id = uuid.uuid4()

    response = client.get(
        f"{URL}/users/{user_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_user_by_id_requires_auth(client):
    response = client.get(f"{URL}/users/{uuid.uuid4()}")
    assert response.status_code == 401

def test_get_user_by_id_invalid_uuid(client, auth_headers):

    response = client.get(
        f"{URL}/users/INVALIDUUID",
        headers=auth_headers
    )

    assert response.status_code == 422
