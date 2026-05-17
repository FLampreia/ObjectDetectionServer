import pytest

from tests.api.conftest import URL

@pytest.mark.parametrize(
    "endpoint",
    [
        f"{URL}/team",
        f"{URL}/team/logged",
    ])
def test_get_team_list_success(
        client,
        first_user_payload,
        auth_headers_factory,
        created_team_factory,
        team_payload_factory,
        endpoint
):
    user1_headers = auth_headers_factory(first_user_payload)

    team1_payload = team_payload_factory()
    team1 = created_team_factory(user1_headers, team1_payload)

    response = client.get(
        endpoint,
        headers=user1_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert any(
        team["id"] == team1["id"]
        for team in data
    )


@pytest.mark.parametrize(
    "endpoint",
    [
        f"{URL}/team",
        f"{URL}/team/logged",
    ])
def test_team_endpoints_require_auth(
        client,
        endpoint
):
    response = client.get(endpoint)
    assert response.status_code == 401


@pytest.mark.parametrize(
    "endpoint",
    [
        f"{URL}/team",
        f"{URL}/team/logged",
    ])
def test_get_team_list_empty(
        client,
        first_user_payload,
        auth_headers_factory,
        endpoint
):
    user1_headers = auth_headers_factory(first_user_payload)

    response = client.get(
        endpoint,
        headers=user1_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []
