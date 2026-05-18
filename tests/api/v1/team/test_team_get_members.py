import uuid

from tests.api.conftest import URL


def test_get_team_members_success(
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
    user2_headers = auth_headers_factory(second_user_payload)

    team1_payload = team_payload_factory()
    team1 = created_team_factory(owner_headers, team1_payload)

    user1_dara = current_user_factory(owner_headers)
    user2_data = current_user_factory(user2_headers)

    team_add_member_factory(owner_headers, team1["id"], user2_data["email"])

    response = client.get(
        f"{URL}/team/{team1["id"]}/members",
        headers=owner_headers,
    )

    assert response.status_code == 200

    data = response.json()

    ids = [member["user_id"] for member in data]

    assert user1_dara["id"] in ids
    assert user2_data["id"] in ids


def test_get_team_members_requires_auth(
        client,
):
    response = client.get(
        f"{URL}/team/{uuid.uuid4()}/members"
    )

    assert response.status_code == 401


def test_get_team_members_team_not_owner(
        client,
        first_user_payload,
        auth_headers_factory,
):
    owner_headers = auth_headers_factory(first_user_payload)

    response = client.get(
        f"{URL}/team/{uuid.uuid4()}/members",
        headers=owner_headers
    )

    assert response.status_code == 403


def test_get_team_members_empty(
        client,
        first_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
        current_user_factory
):
    owner_headers = auth_headers_factory(first_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    current_user = current_user_factory(owner_headers)

    response = client.get(
        f"{URL}/team/{team['id']}/members",
        headers=owner_headers
    )

    assert response.status_code == 200

    data = response.json()

    # owner is already on team
    assert len(data) == 1

    assert data[0]["user_id"] == current_user["id"]


def test_get_team_members_non_member_forbidden(
        client,
        first_user_payload,
        second_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
):
    owner_headers = auth_headers_factory(first_user_payload)
    outsider_headers = auth_headers_factory(second_user_payload)

    team = created_team_factory(
        owner_headers,
        team_payload_factory()
    )

    response = client.get(
        f"{URL}/team/{team['id']}/members",
        headers=outsider_headers
    )

    assert response.status_code == 403