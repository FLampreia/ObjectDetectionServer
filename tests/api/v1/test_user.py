

def test_get_users_success(client, auth_headers):

    response = client.get("/api/v1/users", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

#
# def test_get_users_requires_auth

# from fastapi.testclient import TestClient
#
# from app.api.deps import get_user_service
# from app.main import app
# from app.services.user_service import UserService
# from tests.test_db import TestingSessionLocal
#
# # Setup the TestClient
# client = TestClient(app)
#
#
# # Dependency to override the get_db dependency in the main app
# def override_get_user_service():
#     session = TestingSessionLocal()
#     try:
#         yield UserService(session=session)
#     finally:
#         session.close()
#
#
# app.dependency_overrides[get_user_service] = override_get_user_service
#
#
# def test_create_and_get_user():
#     # Create a new user
#     response = client.post("/api/v1/signin", json={
#         "username": "Test User",
#         "password": "123",
#         "email": "testuser@gmail.com",
#         "full_name": "Test User Full Name"
#     })
#     assert response.status_code == 201
#     created_user = response.json()
#     assert created_user["username"] == "Test User"
#     assert "id" in created_user
#
#     # Fetch the same user
#     get_response = client.get(f"/api/v1/users/{created_user['id']}")
#     assert get_response.status_code == 200
#     fetched_user = get_response.json()
#     assert fetched_user["id"] == created_user["id"]
#     assert fetched_user["username"] == "Test User"
#
# def test_create_and_delete_user():
#     # Create a new user
#     response = client.post("/api/v1/signin", json={
#         "username": "Test User Delete",
#         "password": "123",
#         "email": "testuser_delete@gmail.com",
#         "full_name": "Test User Full Name"
#     })
#     assert response.status_code == 201
#     created_user = response.json()
#     assert created_user["username"] == "Test User Delete"
#     assert "id" in created_user
#     user_id = created_user["id"]
#
#     # Delete the same user
#     delete_response = client.delete(f"/api/v1/users/{user_id}")
#     assert delete_response.status_code == 200
#
#     # Try to fetch the deleted user
#     get_response = client.get(f"/api/v1/users/{user_id}")
#     assert get_response.status_code == 404
#
# def test_create_and_login():
#     # Creaet a new user
#     response = client.post("/api/v1/signin", json={
#         "username": "Test User Signin",
#         "password": "123",
#         "email": "testuser_login@gmail.com",
#         "full_name": "Test User Full Name"
#     })
#     assert response.status_code == 201
#     created_user = response.json()
#     assert created_user["username"] == "Test User Signin"
#     assert "id" in created_user
#     user_id = created_user["id"]
#
#     # Login with same user
#     response = client.post("/api/v1/login", json={
#         "email": "testuser_login@gmail.com",
#         "password": "123"
#     })
#     assert response.status_code == 200
#
#     login_data = response.json()
#     # Check if token exists
#     assert "access_token" in login_data
#     assert "refresh_token" in login_data
#
#     # Checks if token is not empty
#     assert isinstance(login_data["access_token"], str)
#     assert len(login_data["access_token"]) > 0