import pytest
from app import create_app
from config import Config
from database.db import init_db, get_user_by_username


@pytest.fixture
def app(tmp_path):
    test_db = tmp_path / "test_auth.db"

    class LocalTestConfig(Config):
        TESTING = True
        DATABASE_URL = ""
        SQLITE_PATH = str(test_db)
        SECRET_KEY = "auth-secret-test"

    app = create_app(LocalTestConfig)
    with app.app_context():
        init_db()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_register_agent_success(client, app):
    response = client.post("/auth/register", data={
        "username": "sarah_support",
        "email": "sarah@company.com",
        "password": "securepassword123",
        "confirm_password": "securepassword123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome aboard, sarah_support" in response.data

    with app.app_context():
        user = get_user_by_username("sarah_support")
        assert user is not None
        assert user["email"] == "sarah@company.com"
        assert user["password_hash"] != "securepassword123"  # Must be hashed


def test_register_password_mismatch(client):
    response = client.post("/auth/register", data={
        "username": "newagent",
        "email": "new@company.com",
        "password": "password123",
        "confirm_password": "differentpassword"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Passwords do not match." in response.data


def test_register_duplicate_username(client):
    # Register first
    client.post("/auth/register", data={
        "username": "agent_duplicate",
        "email": "agent1@company.com",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)

    # Logout first
    client.get("/auth/logout")

    # Try registering same username
    response = client.post("/auth/register", data={
        "username": "agent_duplicate",
        "email": "agent2@company.com",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"That username is already taken." in response.data


def test_login_invalid_credentials(client):
    response = client.post("/auth/login", data={
        "identifier": "nonexistent",
        "password": "wrongpassword"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid username or password." in response.data


def test_login_and_logout_flow(client):
    # 1. Register agent
    client.post("/auth/register", data={
        "username": "alex_triage",
        "email": "alex@company.com",
        "password": "mypassword123",
        "confirm_password": "mypassword123"
    }, follow_redirects=True)

    # 2. Logout
    logout_resp = client.get("/auth/logout", follow_redirects=True)
    assert b"signed out successfully" in logout_resp.data

    # 3. Login with email
    login_resp = client.post("/auth/login", data={
        "identifier": "alex@company.com",
        "password": "mypassword123"
    }, follow_redirects=True)

    assert login_resp.status_code == 200
    assert b"Welcome back, alex_triage" in login_resp.data
