import uuid

from tests.api.conftest import URL


def test_get_users_success(client, auth_headers, db_user):
    response = client.get(f"{URL}/users", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()

    assert any(u["id"] == str(db_user.id) for u in data)


def test_get_users_requires_auth(client):
    response = client.get(f"{URL}/users")
    assert response.status_code == 401


def test_get_user_by_id_success(client, auth_headers, db_user):
    response = client.get(f"{URL}/users/{db_user.id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(db_user.id)
    assert data["username"] == db_user.username
    assert data["email"] == db_user.email
    assert data["full_name"] == db_user.full_name


def test_get_user_by_id_not_found(client, auth_headers):
    user_id = uuid.uuid4()

    response = client.get(
        f"{URL}/users/{user_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_user_by_id_requires_auth(client):
    response = client.get(f"{URL}/users/{uuid.uuid4()}")
    assert response.status_code == 401


def test_update_user_partial_success(client, auth_headers, current_user):
    response = client.patch(
        f"{URL}/users/{current_user['id']}",
        headers=auth_headers,
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


def test_update_other_user_partial(client, auth_headers, db_user):
    response = client.patch(
        f"{URL}/users/{db_user.id}",
        headers=auth_headers,
        json={
            "username": "new_username",
            "full_name": "New Full Name",
            "password": "newPassword123",
            "current_password": "password123"
        }
    )

    assert response.status_code == 403


def test_update_user_partial_invalid_current_password(client, auth_headers, current_user):
    response = client.patch(
        f"{URL}/users/{current_user['id']}",
        headers=auth_headers,
        json={
            "username": "new_username",
            "full_name": "New Full Name",
            "password": "newPassword123",
            "current_password": "invalidPassword123"
        }
    )

    assert response.status_code == 401


def test_update_user_partial_requires_auth(client, auth_headers, current_user):
    response = client.patch(
        f"{URL}/users/{current_user['id']}",
        json={
            "username": "new_username",
            "full_name": "New Full Name",
            "password": "newPassword123",
            "current_password": "invalidPassword123"
        }
    )

    assert response.status_code == 401


def test_update_user_partial_empty_payload(client, auth_headers, current_user):
    response = client.patch(
        f"{URL}/users/{current_user['id']}",
        headers=auth_headers,
        json={
            "username": None,
            "full_name": None,
            "password": None,
            "current_password": None
        }
    )

    assert response.status_code == 400


def test_update_user_partial_only_username(client, auth_headers, current_user):
    response = client.patch(
        f"{URL}/users/{current_user['id']}",
        headers=auth_headers,
        json={
            "username": "new_username"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["username"] == "new_username"


def test_update_user_partial_only_password(client, auth_headers, current_user):
    response = client.patch(
        f"{URL}/users/{current_user['id']}",
        headers=auth_headers,
        json={
            "password": "newPassword123",
            "current_password": "password123"
        }
    )

    assert response.status_code == 200


def test_update_user_partial_email(client, auth_headers, current_user):
    response = client.patch(
        f"{URL}/users/{current_user['id']}",
        headers=auth_headers,
        json={
            "email": "email@email.com"
        }
    )

    assert response.status_code == 400


def test_delete_user_success(client, auth_headers, current_user):
    response = client.delete(
        f"{URL}/users/{current_user['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert response.json()["success"] is True


def test_delete_other_user(client, auth_headers, db_user):
    response = client.delete(
        f"{URL}/users/{db_user.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


def test_delete_user_requires_auth(client, auth_headers, current_user):
    response = client.delete(
        f"{URL}/users/{current_user['id']}",
    )
    assert response.status_code == 401


def test_full_user_lifecycle_flow(client, authenticated_user):
    access_headers = authenticated_user["access_headers"]
    payload = authenticated_user["user"]

    # Get current user
    me_response = client.get(
        f"{URL}/me",
        headers=access_headers
    )

    assert me_response.status_code == 200

    me_data = me_response.json()

    user_id = me_data["id"]

    # Update user
    update_response = client.patch(
        f"{URL}/users/{user_id}",
        headers=access_headers,
        json={
            "username": "updated_username",
            "full_name": "Updated Full Name",
            "password": "newPassword123",
            "current_password": payload["password"]
        }
    )

    assert update_response.status_code == 200

    updated_data = update_response.json()

    assert updated_data["username"] == "updated_username"
    assert updated_data["full_name"] == "Updated Full Name"

    # Login with new password
    relogin_response = client.post(
        f"{URL}/login",
        json={
            "email": payload["email"],
            "password": "newPassword123"
        }
    )

    assert relogin_response.status_code == 200

    new_access_token = relogin_response.json()["access_token"]

    new_headers = {
        "Authorization": f"Bearer {new_access_token}"
    }

    # Delete user
    delete_response = client.delete(
        f"{URL}/users/{user_id}",
        headers=new_headers
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True

    # Ensure deleted user can no longer login
    failed_login_response = client.post(
        f"{URL}/login",
        json={
            "email": payload["email"],
            "password": "newPassword123"
        }
    )

    assert failed_login_response.status_code == 401
