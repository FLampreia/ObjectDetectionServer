from tests.api.conftest import URL


def test_get_logged_user_team_list_success(
    client,
    auth_headers,
    created_team
):
    response = client.get(
        f"{URL}/team/logged",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert any(
        team["id"] == created_team["id"]
        for team in data
    )


def test_get_logged_user_team_list_requires_auth(client):
    response = client.get(
        f"{URL}/team/logged"
    )

    assert response.status_code == 401


def test_get_logged_user_team_list_empty(
    client,
    auth_headers
):
    response = client.get(
        f"{URL}/team/logged",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []


def test_get_logged_user_team_list_only_returns_user_teams(
    client,
    auth_headers,
    auth_headers_second_user
):
    # first user team
    response1 = client.post(
        f"{URL}/team",
        headers=auth_headers,
        json={"name": "team_user_1"}
    )

    assert response1.status_code == 201

    team_user_1 = response1.json()

    # second user team
    response2 = client.post(
        f"{URL}/team",
        headers=auth_headers_second_user,
        json={"name": "team_user_2"}
    )

    assert response2.status_code == 201

    team_user_2 = response2.json()

    # getting teams for the first user
    response = client.get(
        f"{URL}/team/logged",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    returned_team_ids = [team["id"] for team in data]

    assert team_user_1["id"] in returned_team_ids
    assert team_user_2["id"] not in returned_team_ids