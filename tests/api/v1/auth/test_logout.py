from tests.api.conftest import URL


def test_logout_success(client, auth_headers_factory, first_user_payload):
    user_headers = auth_headers_factory(first_user_payload)
    response = client.post(
        f"{URL}/logout",
        headers=user_headers
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_logout_without_token(client):
    response = client.post(f"{URL}/logout")
    assert response.status_code == 401


def test_logout_with_refresh_token(client, login_user, first_user_payload):
    user1 = login_user(first_user_payload)
    refresh_token = user1["refresh_token"]

    response = client.post(
        f"{URL}/logout",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 401
