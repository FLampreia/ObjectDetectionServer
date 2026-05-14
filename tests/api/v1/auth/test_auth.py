import pytest

from tests.api.conftest import URL


def test_create_user_success(client, user_payload):
    response = client.post(f"{URL}/signin", json=user_payload)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_payload["email"]
    assert data["username"] == user_payload["username"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"username": "differentUsername"},  # same email
        {"email": "different@email.com"},  # same username
        {}  # same username + same email
    ],
    ids=[
        "existing_email",
        "existing_username",
        "duplicate_user"
    ]
)
def test_create_user_conflicts(
        client,
        user_payload,
        overrides
):
    response = client.post("/api/v1/signin", json=user_payload)
    assert response.status_code == 201

    duplicated_payload = {
        **user_payload,
        **overrides,
    }

    response = client.post(f"{URL}/signin", json=duplicated_payload)

    assert response.status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": None},
        {"password": None},
        {"password": "123"},

    ],
    ids=[
        "missing_email",
        "missing_password",
        "short_password"
    ]
)
def test_create_user_invalid_fields(
        client,
        user_payload,
        overrides
):
    invalid_payload = {
        **user_payload,
        **overrides
    }

    response = client.post(f"{URL}/signin", json=invalid_payload)
    assert response.status_code == 422


def test_login_success(client, user_payload):
    client.post(f"{URL}/signin", json=user_payload)

    response = client.post(f"{URL}/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["message"] == "Login Successful"


@pytest.mark.parametrize(
    "overrides, expected_status_code",
    [
        ({"email": "wrong@test.com"}, 401),
        ({"password": "wrongpassword"}, 401),
        ({"email": None}, 422),
        ({"password": None}, 422)
    ],
    ids=[
        "invalid_email",
        "invalid_password",
        "missing_email",
        "missing_password",
    ]
)
def test_login_invalid_credentials(
        client,
        user_payload,
        overrides,
        expected_status_code
):
    client.post(f"{URL}/signin", json=user_payload)

    login_payload = {
        "email": user_payload["email"],
        "password": user_payload["password"],
        **overrides
    }

    response = client.post(
        f"{URL}/login",
        json=login_payload
    )

    assert response.status_code == expected_status_code


def test_me(client, auth_headers):
    response = client.get(f"{URL}/me", headers=auth_headers)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "headers, expected_status",
    [
        (None, 401),
        ({"Authorization": "Bearer invalidtoken"}, 401),
        ({"Authorization": "Bearer"}, 401)
    ],
    ids=[
        "missing_token",
        "invalid_token",
        "empty_token"
    ]
)
def test_me_invalid_token(
        client,
        headers,
        expected_status,
):
    response = client.get(
        f"{URL}/me",
        headers=headers
    )

    assert response.status_code == expected_status


def test_me_with_refresh_token(client, login_data):
    refresh_token = login_data["refresh_token"]

    response = client.get(
        f"{URL}/me",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 401


def test_me_after_logout(client, auth_headers):
    logout = client.post(f"{URL}/logout", headers=auth_headers)
    assert logout.status_code == 200

    me = client.get(f"{URL}/me", headers=auth_headers)

    assert me.status_code == 401


def test_logout_success(client, auth_headers):
    response = client.post(f"{URL}/logout", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_refresh_success(client, login_data):
    refresh_token = login_data["refresh_token"]

    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }

    response = client.post(f"{URL}/refresh", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["message"] == "Refresh Successful"


def test_refresh_with_access_token(client, auth_token):
    response = client.post(
        f"{URL}/refresh",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 401


def test_refresh_token_reuse(client, login_data):
    refresh_token = login_data["refresh_token"]

    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }

    first = client.post(f"{URL}/refresh", headers=headers)
    assert first.status_code == 200

    second = client.post(f"{URL}/refresh", headers=headers)
    assert second.status_code == 401


def test_complete_authentication_flow(client, authenticated_user):
    access_headers = authenticated_user["access_headers"]
    refresh_headers = authenticated_user["refresh_headers"]

    # /me
    me_response = client.get(f"{URL}/me", headers=access_headers)
    assert me_response.status_code == 200

    # /refresh_token
    refresh_response = client.post(f"{URL}/refresh", headers=refresh_headers)
    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data

    # token rotation
    assert refresh_data["access_token"] != authenticated_user["access_token"]
    assert refresh_data["refresh_token"] != authenticated_user["refresh_token"]

    new_access_token = refresh_data["access_token"]
    new_access_headers = {
        "Authorization": f"Bearer {new_access_token}"
    }

    new_refresh_token = refresh_data["refresh_token"]
    new_refresh_headers = {
        "Authorization": f"Bearer {new_refresh_token}"
    }

    # /me
    me_response = client.get(f"{URL}/me", headers=new_access_headers)
    assert me_response.status_code == 200

    # /logout
    logout_response = client.post(f"{URL}/logout", headers=new_access_headers)
    assert logout_response.status_code == 200

    # /me - old token
    me_response = client.get(f"{URL}/me", headers=access_headers)
    assert me_response.status_code == 401

    # /refresh - refresh token revoked after logout
    refresh_response = client.post(f"{URL}/refresh", headers=new_refresh_headers)
    assert refresh_response.status_code == 401

# TODO testes
#     def test_refresh_without_token()
#     def test_logout_requires_auth()
#     PATCH sem current_password ao mudar password
#     PATCH com username já existente
#     DELETE user inexistente
#     GET invalid UUID
#     .
#     9. Algumas fixtures podem ser compostas
#     auth_token
#     auth_headers
#     login_data
#         @pytest.fixture
#         def authenticated_client(client, user_payload):
#     Que devolve:
#         client
#         headers
#         user
#         tokens
#     .
#     padronizar
#         test_<endpoint>_<condition>_<expected_result>
