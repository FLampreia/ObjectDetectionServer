import pytest

from tests.api.conftest import URL


def test_me(client, first_user_payload, auth_headers_factory):
    user_headers = auth_headers_factory(first_user_payload)

    response = client.get(
        f"{URL}/me",
        headers=user_headers
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "headers",
    [
        None,
        {"Authorization": "Bearer invalidtoken"},
        {"Authorization": "Bearer"}
    ],
    ids=[
        "missing_token",
        "invalid_token",
        "empty_token"
    ]
)
def test_me_invalid_token(
        client,
        headers
):
    response = client.get(
        f"{URL}/me",
        headers=headers
    )

    assert response.status_code == 401


def test_me_with_refresh_token(client, login_user, first_user_payload):
    user1 = login_user(first_user_payload)
    refresh_token = user1["refresh_token"]

    response = client.get(
        f"{URL}/me",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 401


def test_me_after_logout(client, first_user_payload, auth_headers_factory):
    user_headers = auth_headers_factory(first_user_payload)

    logout = client.post(
        f"{URL}/logout",
        headers=user_headers
    )
    assert logout.status_code == 200

    me = client.get(
        f"{URL}/me",
        headers=user_headers
    )

    assert me.status_code == 401
