import pytest

from tests.api.conftest import URL


def test_create_team_success(client, auth_headers):
    response = client.post(
        f"{URL}/team",
        headers=auth_headers,
        json={
            "name": "TestTeam"
        }
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "TestTeam"


def test_create_team_requires_auth(client):
    response = client.post(
        f"{URL}/team",
        json={
            "name": "TestTeam"
        }
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": None},
        {},
    ],
    ids=[
        "name_empty",
        "name_missing",
        "payload_missing",
    ]
)
def test_create_team_invalid_name(client, auth_headers, payload):
    response = client.post(
        f"{URL}/team",
        headers=auth_headers,
        json=payload
    )
    assert response.status_code == 422


def test_create_team_duplicate_name(client, auth_headers):
    payload = {"name": "TestTeam"}

    response1 = client.post(
        f"{URL}/team",
        headers=auth_headers,
        json=payload
    )
    assert response1.status_code == 201

    response2 = client.post(
        f"{URL}/team",
        headers=auth_headers,
        json=payload
    )

    assert response2.status_code == 409