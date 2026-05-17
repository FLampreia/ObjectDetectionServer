import uuid

from tests.api.conftest import URL



def test_full_user_lifecycle_flow(
        client,
        first_user_payload,
        auth_headers_factory,
):
    user1_headers = auth_headers_factory(first_user_payload)


    # Get current user
    me_response = client.get(
        f"{URL}/me",
        headers=user1_headers
    )

    assert me_response.status_code == 200

    me_data = me_response.json()

    user_id = me_data["id"]

    # Update user
    update_response = client.patch(
        f"{URL}/users/{user_id}",
        headers=user1_headers,
        json={
            "username": "updated_username",
            "full_name": "Updated Full Name",
            "password": "newPassword123",
            "current_password": first_user_payload["password"]
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
            "email": first_user_payload["email"],
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
            "email": first_user_payload["email"],
            "password": "newPassword123"
        }
    )

    assert failed_login_response.status_code == 401