from tests.api.conftest import URL


def test_logout_success(client, auth_headers):
    response = client.post(f"{URL}/logout", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_logout_without_token(client):
    response = client.post(f"{URL}/logout")
    assert response.status_code == 401
