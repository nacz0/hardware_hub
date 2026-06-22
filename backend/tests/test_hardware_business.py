import os
import sys
from pathlib import Path

os.environ.setdefault("JWT_SECRET", "test-secret-value-that-is-long-enough")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from fastapi.testclient import TestClient

from app import database
from app.auth import create_access_token
from app.main import app
from app.users import create_user


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "hardware_hub.db")
    database.initialize_database()

    admin = create_user("admin@example.com", "password123", "admin")
    user = create_user("user@example.com", "password123", "user")

    with TestClient(app) as test_client:
        yield test_client, admin, user


def auth_headers(user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def create_hardware_item(
    test_client: TestClient,
    admin: dict,
    *,
    status: str,
    assigned_to: str | None = None,
) -> dict:
    response = test_client.post(
        "/hardware",
        json={
            "name": f"Business critical {status} device",
            "brand": "Test",
            "status": status,
            "assignedTo": assigned_to,
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 201
    return response.json()


def test_user_cannot_rent_hardware_with_repair_status(client):
    test_client, admin, user = client
    hardware = create_hardware_item(test_client, admin, status="Repair")

    response = test_client.post(
        f"/hardware/{hardware['id']}/rent",
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Hardware can only be rented when Available"


def test_user_cannot_rent_hardware_already_in_use(client):
    test_client, admin, user = client
    hardware = create_hardware_item(
        test_client,
        admin,
        status="In Use",
        assigned_to="other@example.com",
    )

    response = test_client.post(
        f"/hardware/{hardware['id']}/rent",
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Hardware can only be rented when Available"


def test_user_can_rent_hardware_only_when_available(client):
    test_client, admin, user = client
    hardware = create_hardware_item(test_client, admin, status="Available")

    response = test_client.post(
        f"/hardware/{hardware['id']}/rent",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "In Use"
    assert response.json()["assigned_to"] == user["email"]


def test_user_cannot_return_hardware_that_is_not_in_use(client):
    test_client, admin, user = client
    hardware = create_hardware_item(test_client, admin, status="Available")

    response = test_client.post(
        f"/hardware/{hardware['id']}/return",
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Hardware can only be returned when In Use"


def test_regular_user_cannot_create_another_user(client):
    test_client, _admin, user = client

    response = test_client.post(
        "/admin/users",
        json={
            "email": "created-by-user@example.com",
            "password": "password123",
            "role": "user",
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 403


def test_admin_can_create_user(client):
    test_client, admin, _user = client

    response = test_client.post(
        "/admin/users",
        json={
            "email": "New.User@Example.com",
            "password": "password123",
            "role": "user",
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "email": "new.user@example.com",
        "role": "user",
        "created_at": response.json()["created_at"],
    }
