import pytest

from tests.api.conftest import URL


def test_update_user_partial_success(
        client,
        first_user_payload,
        auth_headers_factory,
        current_user_factory
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user_factory(user1_headers)

    response = client.patch(
        f"{URL}/users/{user1['id']}",
        headers=user1_headers,
        json={
            "username": "new_username",
            "full_name": "New Full Name",
            "password": "newPassword123",
            "current_password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "new_username"
    assert data["full_name"] == "New Full Name"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "new_username",
            "full_name": "New Full Name",
            "password": "newPassword123",
            "current_password": "invalidPassword123"
        },
        {
            "username": None,
            "full_name": None,
            "password": None,
            "current_password": None
        },
        {
            "email": "email@email.com"
        },
        {
            "password": "newPassword123"
        }
    ],
    ids=[
        "invalid_current_password",
        "empty_payload",
        "email_not_allowed",
        "missing_current_password",
    ]
)
def test_update_user_partial_invalid_cases(
        client,
        first_user_payload,
        auth_headers_factory,
        current_user_factory,
        payload
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user_factory(user1_headers)

    response = client.patch(
        f"{URL}/users/{user1['id']}",
        headers=user1_headers,
        json=payload
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "new_username"
        },
        {
            "password": "newPassword123",
            "current_password": "password123"
        },
        {
            "full_name": "New Full Name"
        },
    ],
    ids=[
        "only_username",
        "only_password",
        "only_full_name",
    ]
)
def test_update_user_partial_single_field_success(
        client,
        first_user_payload,
        auth_headers_factory,
        current_user_factory,
        payload
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user_factory(user1_headers)

    response = client.patch(
        f"{URL}/users/{user1['id']}",
        headers=user1_headers,
        json=payload
    )

    assert response.status_code == 200


def test_update_other_user_partial(
        client,
        first_user_payload,
        auth_headers_factory,
        create_user_factory,
        second_user_payload,
):
    user1_headers = auth_headers_factory(first_user_payload)
    user2 = create_user_factory(second_user_payload)

    response = client.patch(
        f"{URL}/users/{user2["id"]}",
        headers=user1_headers,
        json={
            "username": "new_username",
            "full_name": "New Full Name",
            "password": "newPassword123",
            "current_password": "password123"
        }
    )

    assert response.status_code == 403


def test_update_user_partial_requires_auth(
        client,
        first_user_payload,
        auth_headers_factory,
        current_user_factory,
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user_factory(user1_headers)

    response = client.patch(
        f"{URL}/users/{user1['id']}",
        json={
            "username": "new_username"
        }
    )

    assert response.status_code == 401


def test_update_user_partial_username_already_exists(
        client,
        first_user_payload,
        auth_headers_factory,
        create_user_factory,
        second_user_payload,
        current_user_factory
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user_factory(user1_headers)
    user2 = create_user_factory(second_user_payload)

    response = client.patch(
        f"{URL}/users/{user1['id']}",
        headers=user1_headers,
        json={
            "username": user2["username"]
        }
    )

    assert response.status_code == 409
