from tests.api.conftest import URL


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
