import uuid

import pytest

from tests.api.conftest import URL


def test_remove_team_member_success(
        client,
        first_user_payload,
        second_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
        team_add_member_factory,
        current_user_factory
):
    owner_headers = auth_headers_factory(first_user_payload)
    member_headers = auth_headers_factory(second_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    member_data = current_user_factory(member_headers)

    team_add_member_factory(
        owner_headers,
        team["id"],
        member_data["email"]
    )

    response = client.request(
        "DELETE",
        f"{URL}/team/{team['id']}/remove",
        json={
            "email": member_data["email"]
        },
        headers=owner_headers,
    )

    assert response.status_code == 200

    # confirm removal
    members_response = client.get(
        f"{URL}/team/{team['id']}/members",
        headers=owner_headers
    )

    members_data = members_response.json()

    ids = [member["user_id"] for member in members_data]

    assert member_data["id"] not in ids


def test_remove_team_member_requires_auth(
        client,
):
    response = client.request(
        "DELETE",
        f"{URL}/team/{uuid.uuid4()}/remove",
        json={
            "email": "test@test.com"
        }
    )

    assert response.status_code == 401


def test_remove_team_member_team_not_owner(
        client,
        first_user_payload,
        second_user_payload,
        auth_headers_factory,
):
    owner_headers = auth_headers_factory(first_user_payload)

    response = client.request(
        "DELETE",
        f"{URL}/team/{uuid.uuid4()}/remove",
        headers=owner_headers,
        json={
            "email": second_user_payload["email"]
        }
    )

    assert response.status_code == 403


def test_remove_team_member_user_not_in_team(
        client,
        first_user_payload,
        second_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
):
    owner_headers = auth_headers_factory(first_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    response = client.request(
        "DELETE",
        f"{URL}/team/{team['id']}/remove",
        headers=owner_headers,
        json={
            "email": second_user_payload["email"]
        }
    )

    assert response.status_code == 404


def test_remove_team_member_non_owner_forbidden(
        client,
        first_user_payload,
        second_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
        team_add_member_factory,
        current_user_factory
):
    owner_headers = auth_headers_factory(first_user_payload)
    member_headers = auth_headers_factory(second_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    member_data = current_user_factory(member_headers)

    team_add_member_factory(
        owner_headers,
        team["id"],
        member_data["email"]
    )

    response = client.request(
        "DELETE",
        f"{URL}/team/{team['id']}/remove",
        headers=member_headers,
        json={
            "email": first_user_payload["email"]
        }
    )

    assert response.status_code == 403


@pytest.mark.parametrize("invalid_team_id", [
    "invalid-uuid",
    "123",
    "abc",
])
def test_remove_team_member_invalid_team_id(
        client,
        first_user_payload,
        auth_headers_factory,
        invalid_team_id
):
    owner_headers = auth_headers_factory(first_user_payload)

    response = client.request(
        "DELETE",
        f"{URL}/team/{invalid_team_id}/remove",
        headers=owner_headers,
        json={
            "email": "test@test.com"
        }
    )

    assert response.status_code == 422


@pytest.mark.parametrize("payload", [
    {},
    {"invalid": "field"},
])
def test_remove_team_member_missing_email(
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

    response = client.request(
        "DELETE",
        f"{URL}/team/{team['id']}/remove",
        headers=owner_headers,
        json=payload
    )

    assert response.status_code == 422


def test_remove_team_member_remove_owner_forbidden(
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

    response = client.request(
        "DELETE",
        f"{URL}/team/{team['id']}/remove",
        headers=owner_headers,
        json={
            "email": first_user_payload["email"]
        }
    )

    assert response.status_code == 403