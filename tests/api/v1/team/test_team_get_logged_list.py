from tests.api.conftest import URL



def test_get_logged_user_team_list_only_returns_user_teams(
    client,
    first_user_payload,
    second_user_payload,
    auth_headers_factory,
    created_team_factory,
    team_payload_factory
):
    user1_headers = auth_headers_factory(first_user_payload)
    user2_headers = auth_headers_factory(second_user_payload)

    team1_payload = team_payload_factory()
    team2_payload = team_payload_factory()
    team1 = created_team_factory(user1_headers, team1_payload)
    team2 = created_team_factory(user2_headers, team2_payload)

    response = client.get(f"{URL}/team/logged", headers=user1_headers)

    data = response.json()

    assert all(team["id"] == team1["id"] for team in data)
    assert all(team["id"] != team2["id"] for team in data)