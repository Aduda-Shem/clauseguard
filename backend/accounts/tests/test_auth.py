import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_register_creates_user_and_returns_token(client):
    resp = client.post(
        "/api/auth/register/",
        {"username": "alice", "email": "alice@example.com", "password": "testpass123"},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["username"] == "alice"
    assert "token" in body
    assert User.objects.filter(username="alice").exists()


@pytest.mark.django_db
def test_register_rejects_duplicate_username(client):
    User.objects.create_user(username="alice", password="testpass123")
    resp = client.post(
        "/api/auth/register/",
        {"username": "alice", "email": "a2@example.com", "password": "testpass123"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/auth/register/",
        {"username": "alice", "email": "alice@example.com", "password": "short"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_login_with_valid_credentials_returns_token(client):
    User.objects.create_user(username="alice", password="testpass123")
    resp = client.post("/api/auth/login/", {"username": "alice", "password": "testpass123"}, format="json")
    assert resp.status_code == 200
    assert "token" in resp.json()


@pytest.mark.django_db
def test_login_with_wrong_password_rejected(client):
    User.objects.create_user(username="alice", password="testpass123")
    resp = client.post("/api/auth/login/", {"username": "alice", "password": "wrong"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_me_requires_authentication(client):
    resp = client.get("/api/auth/user/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_returns_current_user(client):
    user = User.objects.create_user(username="alice", password="testpass123")
    client.force_authenticate(user=user)
    resp = client.get("/api/auth/user/")
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


@pytest.mark.django_db
def test_logout_invalidates_token(client):
    login_resp = client.post(
        "/api/auth/register/",
        {"username": "alice", "email": "alice@example.com", "password": "testpass123"},
        format="json",
    )
    token = login_resp.json()["token"]

    authed_client = APIClient()
    authed_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    assert authed_client.get("/api/auth/user/").status_code == 200

    assert authed_client.post("/api/auth/logout/").status_code == 204
    assert authed_client.get("/api/auth/user/").status_code == 401
