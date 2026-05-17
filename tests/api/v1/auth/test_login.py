import pytest

from tests.api.conftest import URL


def test_login_success(client, first_user_payload):
    client.post(f"{URL}/signin", json=first_user_payload)

    response = client.post(f"{URL}/login", json={
        "email": first_user_payload["email"],
        "password": first_user_payload["password"]
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
        first_user_payload,
        overrides,
        expected_status_code
):
    client.post(f"{URL}/signin", json=first_user_payload)

    login_payload = {
        "email": first_user_payload["email"],
        "password": first_user_payload["password"],
        **overrides
    }

    response = client.post(
        f"{URL}/login",
        json=login_payload
    )

    assert response.status_code == expected_status_code
