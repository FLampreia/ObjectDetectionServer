from tests.api.conftest import URL


def test_refresh_success(client, login_user, first_user_payload):
    user1 = login_user(first_user_payload)
    refresh_token = user1["refresh_token"]

    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }

    response = client.post(f"{URL}/refresh", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["message"] == "Refresh Successful"


def test_refresh_with_access_token(client, first_user_payload, auth_headers_factory):
    user_headers = auth_headers_factory(first_user_payload)

    response = client.post(
        f"{URL}/refresh",
        headers={"Authorization": f"Bearer {user_headers}"}
    )

    assert response.status_code == 401


def test_refresh_token_reuse(client, login_user, first_user_payload):
    user1 = login_user(first_user_payload)
    refresh_token = user1["refresh_token"]

    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }

    first = client.post(f"{URL}/refresh", headers=headers)
    assert first.status_code == 200

    second = client.post(f"{URL}/refresh", headers=headers)
    assert second.status_code == 401


def test_refresh_without_token(client):
    response = client.post(f"{URL}/refresh")
    assert response.status_code == 401
