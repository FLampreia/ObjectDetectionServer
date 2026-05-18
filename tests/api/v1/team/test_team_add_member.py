import uuid

import pytest

from tests.api.conftest import URL


def test_add_team_member_success(
        client,
        first_user_payload,
        second_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
        current_user_factory
):
    owner_headers = auth_headers_factory(first_user_payload)
    user2_headers = auth_headers_factory(second_user_payload)

    team1_payload = team_payload_factory()
    team1 = created_team_factory(owner_headers, team1_payload)

    user2_data = current_user_factory(user2_headers)

    response = client.post(
        f"{URL}/team/{team1["id"]}/add",
        json={
            "email": user2_data["email"],
        },
        headers=owner_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["team_id"] == str(team1["id"])
    assert data["user_id"] == str(user2_data["id"])
    assert data["role"] == "member"


def test_add_team_member_requires_auth(
        client,
):
    response = client.post(
        f"{URL}/team/{uuid.uuid4()}/add",
        json={
            "email": "test@test.com"
        }
    )

    assert response.status_code == 401


def test_add_team_member_user_not_found(
        client,
        first_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
):
    owner_headers = auth_headers_factory(first_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    response = client.post(
        f"{URL}/team/{team['id']}/add",
        headers=owner_headers,
        json={
            "email": "notfound@test.com"
        }
    )

    assert response.status_code == 404


def test_add_team_member_already_in_team(
        client,
        first_user_payload,
        second_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
):
    owner_headers = auth_headers_factory(first_user_payload)
    member_headers = auth_headers_factory(second_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    # first add
    first_response = client.post(
        f"{URL}/team/{team['id']}/add",
        headers=owner_headers,
        json={
            "email": second_user_payload["email"]
        }
    )

    assert first_response.status_code == 200

    # duplicate add
    response = client.post(
        f"{URL}/team/{team['id']}/add",
        headers=owner_headers,
        json={
            "email": second_user_payload["email"]
        }
    )

    assert response.status_code in [400, 409]


def test_add_team_member_non_owner_forbidden(
        client,
        first_user_payload,
        second_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
):
    owner_headers = auth_headers_factory(first_user_payload)
    member_headers = auth_headers_factory(second_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    response = client.post(
        f"{URL}/team/{team['id']}/add",
        headers=member_headers,
        json={
            "email": first_user_payload["email"]
        }
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "invalid_team_id",
    [
        "invalid-uuid",
        "123",
        "abc",
    ]
)
def test_add_team_member_invalid_team_id(
        client,
        first_user_payload,
        auth_headers_factory,
        invalid_team_id
):
    owner_headers = auth_headers_factory(first_user_payload)

    response = client.post(
        f"{URL}/team/{invalid_team_id}/add",
        headers=owner_headers,
        json={
            "email": "test@test.com"
        }
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"role": "member"},
    ],
    ids=[
        "empty",
        "member_payload"
    ]
)
def test_add_team_member_missing_email(
        client,
        first_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
        payload
):
    owner_headers = auth_headers_factory(first_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    response = client.post(
        f"{URL}/team/{team['id']}/add",
        headers=owner_headers,
        json=payload
    )

    assert response.status_code == 422
