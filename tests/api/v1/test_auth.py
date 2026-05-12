import pytest

def test_create_user_success(client, user_payload):
    response = client.post("/api/v1/signin", json=user_payload)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_payload["email"]
    assert data["username"] == user_payload["username"]

def test_create_user_existing_email(client, user_payload):
    response = client.post("/api/v1/signin", json=user_payload)
    assert response.status_code == 201
    response = client.post("/api/v1/signin", json=user_payload)
    assert response.status_code == 409

def test_create_user_existing_username(client, user_payload):
    response = client.post("/api/v1/signin", json=user_payload)
    assert response.status_code == 201

    duplicated_username_payload = {
        **user_payload,
        "email": "different@email.com"
    }

    response = client.post("/api/v1/signin", json=duplicated_username_payload)
    assert response.status_code == 409

def test_create_user_missing_email(client, user_payload):
    response = client.post("/api/v1/signin", json=user_payload)
    assert response.status_code == 201

    missing_email_payload = {
        **user_payload,
        "email": None
    }

    response = client.post("/api/v1/signin", json=missing_email_payload)
    assert response.status_code == 422

# Works for missing or for password with less than 8 characters
def test_create_user_missing_password(client, user_payload):
    response = client.post("/api/v1/signin", json=user_payload)
    assert response.status_code == 201

    missing_password_payload = {
        **user_payload,
        "password": None
    }

    response = client.post("/api/v1/signin", json=missing_password_payload)
    assert response.status_code == 422


def test_login_success(client, user_payload):
    client.post("/api/v1/signin", json=user_payload)

    response = client.post("/api/v1/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["message"] == "Login Successful"


def test_me(client, auth_headers):
    response = client.get("/api/v1/me", headers=auth_headers)

    assert response.status_code == 200


def test_logout_success(client, auth_headers):
    response = client.post("/api/v1/logout", headers=auth_headers)

    assert response.status_code == 200


def test_refresh_success(client, login_data):
    refresh_token = login_data["refresh_token"]

    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }

    response = client.post("/api/v1/refresh", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["message"] == "Refresh Successful"

def test_login_invalid_credentials(client):
    response = client.post("/api/v1/login", json={
        "email": "wrong@test.com",
        "password": "wrongpassword"
    })

    assert response.status_code == 401

def test_create_duplicate_user(client, user_payload):
    client.post("/api/v1/signin", json=user_payload)

    response = client.post("/api/v1/signin", json=user_payload)

    assert response.status_code == 409

def test_me_without_token(client):
    response = client.get("/api/v1/me")

    assert response.status_code == 401

def test_me_invalid_token(client):
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )

    assert response.status_code == 401

def test_refresh_with_access_token(client, auth_token):

    response = client.post(
        "/api/v1/refresh",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 401

def test_me_with_refresh_token(client, login_data):

    refresh_token = login_data["refresh_token"]

    response = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 401

def test_refresh_token_reuse(client, login_data):

    refresh_token = login_data["refresh_token"]

    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }

    first = client.post("/api/v1/refresh", headers=headers)
    assert first.status_code == 200

    second = client.post("/api/v1/refresh", headers=headers)
    assert second.status_code == 401

def test_access_after_logout(client, auth_headers):

    logout = client.post("/api/v1/logout", headers=auth_headers)
    assert logout.status_code == 200

    me = client.get("/api/v1/me", headers=auth_headers)

    assert me.status_code == 401

def test_full_auth_flow(client, user_payload):

    # /signin
    response = client.post("/api/v1/signin", json=user_payload)
    assert response.status_code == 201

    # /login
    response = client.post("/api/v1/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })
    assert response.status_code == 200

    access_token = response.json()["access_token"]
    refresh_token = response.json()["refresh_token"]

    access_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    refresh_headers = {
        "Authorization": f"Bearer {refresh_token}"
    }

    # /me
    response = client.get("/api/v1/me", headers=access_headers)
    assert response.status_code == 200

    # /refresh_token
    response = client.post("/api/v1/refresh", headers=refresh_headers)
    assert response.status_code == 200

    new_access_token = response.json()["access_token"]
    new_access_headers = {
        "Authorization": f"Bearer {new_access_token}"
    }

    new_refresh_token = response.json()["refresh_token"]
    new_refresh_headers = {
        "Authorization": f"Bearer {new_refresh_token}"
    }

    # /me
    response = client.get("/api/v1/me", headers=new_access_headers)
    assert response.status_code == 200

    # /logout
    response = client.post("/api/v1/logout", headers=new_access_headers)
    assert response.status_code == 200

    # /me - old token
    response = client.get("/api/v1/me", headers=access_headers)
    assert response.status_code == 401

    # /refresh - old token
    response = client.post("/api/v1/refresh", headers=new_refresh_headers)
    assert response.status_code == 401