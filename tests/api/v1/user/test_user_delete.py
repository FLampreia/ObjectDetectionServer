from tests.api.conftest import URL


def test_delete_user_success(client, auth_headers, current_user):
    response = client.delete(
        f"{URL}/users/{current_user['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert response.json()["success"] is True

# delete is only possible for the logged account
# cannot delete other account besides the logged one
def test_delete_other_user(client, auth_headers, create_second_user):
    response = client.delete(
        f"{URL}/users/{create_second_user["id"]}",
        headers=auth_headers,
    )

    assert response.status_code == 403


def test_delete_user_requires_auth(client, auth_headers, current_user):
    response = client.delete(
        f"{URL}/users/{current_user['id']}",
    )
    assert response.status_code == 401
