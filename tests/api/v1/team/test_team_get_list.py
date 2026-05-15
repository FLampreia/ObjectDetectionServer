from tests.api.conftest import URL


def test_get_team_list_success(
    client,
    auth_headers,
    created_team
):
    response = client.get(
        f"{URL}/team",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert any(
        team["id"] == created_team["id"]
        for team in data
    )


def test_get_team_list_requires_auth(client):
    response = client.get(
        f"{URL}/team"
    )

    assert response.status_code == 401


def test_get_team_list_empty(client, auth_headers):
    response = client.get(
        f"{URL}/team",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []