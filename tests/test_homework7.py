import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.main import app, get_db


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def register_and_login(client, username="user1", password="test123", is_read_only=False):
    client.post(
        "/auth/register",
        json={
            "username": username,
            "password": password,
            "is_read_only": is_read_only,
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    return response.json()["user_id"]


# 1. /auth/register

def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "user1",
            "password": "test123",
            "is_read_only": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "user1"
    assert response.json()["is_read_only"] is False


def test_register_duplicate_username(client):
    payload = {
        "username": "user1",
        "password": "test123",
        "is_read_only": False,
    }

    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"


# 2. /auth/login

def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "username": "user2",
            "password": "test123",
            "is_read_only": False,
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "user2",
            "password": "test123",
        },
    )

    assert response.status_code == 200
    assert "user_id" in response.json()
    assert "Login successful" in response.json()["message"]


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "username": "user3",
            "password": "test123",
            "is_read_only": False,
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "user3",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


# 3. /auth/logout

def test_logout_success(client):
    user_id = register_and_login(client, "user4", "test123")

    response = client.post(
        "/auth/logout",
        headers={"X-User-Id": str(user_id)},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Logout successful"


def test_logout_without_header(client):
    response = client.post("/auth/logout")

    assert response.status_code == 401
    assert response.json()["detail"] == "X-User-Id header is required"


# 4. POST /faculties

def test_create_faculty_success(client):
    user_id = register_and_login(client, "admin1", "test123")

    response = client.post(
        "/faculties",
        json={"name": "Computer Science"},
        headers={"X-User-Id": str(user_id)},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Computer Science"


def test_create_faculty_forbidden_for_read_only_user(client):
    user_id = register_and_login(
        client,
        username="readonly1",
        password="test123",
        is_read_only=True,
    )

    response = client.post(
        "/faculties",
        json={"name": "Math"},
        headers={"X-User-Id": str(user_id)},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Read-only user cannot modify data"


# 5. GET /faculties

def test_get_faculties_success(client):
    user_id = register_and_login(client, "admin2", "test123")

    client.post(
        "/faculties",
        json={"name": "Physics"},
        headers={"X-User-Id": str(user_id)},
    )

    response = client.get(
        "/faculties",
        headers={"X-User-Id": str(user_id)},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Physics"


def test_get_faculties_without_auth(client):
    response = client.get("/faculties")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"