import pytest

from tests.api.conftest import URL


def test_me(client, auth_headers):
    response = client.get(f"{URL}/me", headers=auth_headers)

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
