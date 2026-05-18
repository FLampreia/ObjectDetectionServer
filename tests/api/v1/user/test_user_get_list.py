from tests.api.conftest import URL


def test_get_users_success(
        client,
        first_user_payload,
        auth_headers_factory,
        current_user_factory
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user_factory(user1_headers)

    response = client.get(f"{URL}/users", headers=user1_headers)
    assert response.status_code == 200

    data = response.json()

    assert any(u["id"] == user1["id"] for u in data)


def test_get_users_requires_auth(
        client
):
    response = client.get(f"{URL}/users")
    assert response.status_code == 401
