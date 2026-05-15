import uuid

from tests.api.conftest import URL


def test_delete_team_success(client, auth_headers, created_team):
    response = client.delete(
        f"{URL}/team/{created_team["id"]}",
        headers=auth_headers
    )

    assert response.status_code == 200


def test_delete_team_requires_auth(client, created_team):
    response = client.delete(
        f"{URL}/team/{created_team['id']}"
    )

    assert response.status_code == 401


def test_delete_team_team_not_found(client, auth_headers):
    response = client.delete(
        f"{URL}/team/{uuid.uuid4()}",
        headers=auth_headers
    )

    assert response.status_code == 404

def test_delete_team_non_owner_forbidden(
        client,
        auth_headers_second_user,
        created_team
):
    response = client.delete(
        f"{URL}/team/{created_team['id']}",
        headers=auth_headers_second_user
    )

    assert response.status_code == 403


def test_delete_team_invalid_team_id(client, auth_headers):
    response = client.delete(
        f"{URL}/team/invalid-uuid",
        headers=auth_headers
    )

    assert response.status_code == 422


def test_delete_team_already_deleted(client, auth_headers, created_team):
    response1 = client.delete(
        f"{URL}/team/{created_team['id']}",
        headers=auth_headers
    )

    assert response1.status_code == 200

    response2 = client.delete(
        f"{URL}/team/{created_team['id']}",
        headers=auth_headers
    )

    assert response2.status_code == 404
