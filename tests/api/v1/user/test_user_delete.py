from tests.api.conftest import URL


def test_delete_user_success(
        client,
        first_user_payload,
        auth_headers_factory,
        current_user
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user(user1_headers)

    response = client.delete(
        f"{URL}/users/{user1['id']}",
        headers=user1_headers,
    )

    assert response.status_code == 200

    assert response.json()["success"] is True


# delete is only possible for the logged account
# cannot delete other account besides the logged one
def test_delete_other_user(
        client,
        first_user_payload,
        auth_headers_factory,
        create_user_factory,
        second_user_payload
):
    user1_headers = auth_headers_factory(first_user_payload)
    user2 = create_user_factory(second_user_payload)

    response = client.delete(
        f"{URL}/users/{user2["id"]}",
        headers=user1_headers,
    )

    assert response.status_code == 403


def test_delete_user_requires_auth(
        client,
        first_user_payload,
        auth_headers_factory,
        current_user
):
    user1_headers = auth_headers_factory(first_user_payload)
    user1 = current_user(user1_headers)

    response = client.delete(
        f"{URL}/users/{user1['id']}",
    )
    assert response.status_code == 401
