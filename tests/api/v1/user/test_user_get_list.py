from tests.api.conftest import URL


def test_get_users_success(client, auth_headers, current_user):
    response = client.get(f"{URL}/users", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()

    assert any(u["id"] == current_user["id"] for u in data)


def test_get_users_requires_auth(client):
    response = client.get(f"{URL}/users")
    assert response.status_code == 401
