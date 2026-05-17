import uuid

from tests.api.conftest import URL


def test_delete_team_success(
        client,
        first_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory
):
    user1_headers = auth_headers_factory(first_user_payload)

    team1_payload = team_payload_factory()
    team1 = created_team_factory(user1_headers, team1_payload)

    response = client.delete(
        f"{URL}/team/{team1["id"]}",
        headers=user1_headers
    )

    assert response.status_code == 200


def test_delete_team_requires_auth(
        client,
        first_user_payload,
        auth_headers_factory,
        created_team_factory,
team_payload_factory
):
    user1_headers = auth_headers_factory(first_user_payload)

    team1_payload = team_payload_factory()
    team1 = created_team_factory(user1_headers, team1_payload)

    response = client.delete(
        f"{URL}/team/{team1['id']}"
    )

    assert response.status_code == 401


def test_delete_team_team_not_found(
        client,
        first_user_payload,
        auth_headers_factory,
):
    user1_headers = auth_headers_factory(first_user_payload)

    response = client.delete(
        f"{URL}/team/{uuid.uuid4()}",
        headers=user1_headers
    )

    assert response.status_code == 404


def test_delete_team_non_owner_forbidden(
        client,
        first_user_payload,
        auth_headers_factory,
        second_user_payload,
        created_team_factory,
        team_payload_factory
):
    user1_headers = auth_headers_factory(first_user_payload)
    user2_headers = auth_headers_factory(second_user_payload)

    team1_payload = team_payload_factory()
    team1 = created_team_factory(user1_headers, team1_payload)

    response = client.delete(
        f"{URL}/team/{team1['id']}",
        headers=user2_headers
    )

    assert response.status_code == 403


def test_delete_team_invalid_team_id(
        client,
        first_user_payload,
        auth_headers_factory,
):
    user1_headers = auth_headers_factory(first_user_payload)

    response = client.delete(
        f"{URL}/team/invalid-uuid",
        headers=user1_headers
    )

    assert response.status_code == 422


def test_delete_team_already_deleted(
        client,
        first_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory
):
    user1_headers = auth_headers_factory(first_user_payload)

    team1_payload = team_payload_factory()
    team1 = created_team_factory(user1_headers, team1_payload)

    response1 = client.delete(
        f"{URL}/team/{team1['id']}",
        headers=user1_headers
    )

    assert response1.status_code == 200

    response2 = client.delete(
        f"{URL}/team/{team1['id']}",
        headers=user1_headers
    )

    assert response2.status_code == 404
