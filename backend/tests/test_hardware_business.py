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


def test_user_can_rent_only_available_hardware(client):
    test_client, _admin, user = client

    rented = test_client.post(
        "/hardware/1/rent",
        headers=auth_headers(user),
    )

    assert rented.status_code == 200
    assert rented.json()["status"] == "In Use"
    assert rented.json()["assigned_to"] == user["email"]

    already_in_use = test_client.post(
        "/hardware/1/rent",
        headers=auth_headers(user),
    )
    repair = test_client.post(
        "/hardware/3/rent",
        headers=auth_headers(user),
    )
    unknown = test_client.post(
        "/hardware/10/rent",
        headers=auth_headers(user),
    )

    assert already_in_use.status_code == 400
    assert repair.status_code == 400
    assert unknown.status_code == 400


def test_user_can_return_only_in_use_hardware(client):
    test_client, _admin, user = client

    returned = test_client.post(
        "/hardware/2/return",
        headers=auth_headers(user),
    )

    assert returned.status_code == 200
    assert returned.json()["status"] == "Available"
    assert returned.json()["assigned_to"] is None

    not_in_use = test_client.post(
        "/hardware/2/return",
        headers=auth_headers(user),
    )

    assert not_in_use.status_code == 400


def test_missing_hardware_returns_404(client):
    test_client, admin, user = client

    rent_response = test_client.post(
        "/hardware/999/rent",
        headers=auth_headers(user),
    )
    delete_response = test_client.delete(
        "/hardware/999",
        headers=auth_headers(admin),
    )

    assert rent_response.status_code == 404
    assert delete_response.status_code == 404


def test_regular_user_cannot_use_admin_hardware_actions(client):
    test_client, _admin, user = client

    create_response = test_client.post(
        "/hardware",
        json={"name": "Managed laptop", "status": "Available"},
        headers=auth_headers(user),
    )
    repair_response = test_client.post(
        "/hardware/1/repair",
        headers=auth_headers(user),
    )
    delete_response = test_client.delete(
        "/hardware/1",
        headers=auth_headers(user),
    )

    assert create_response.status_code == 403
    assert repair_response.status_code == 403
    assert delete_response.status_code == 403


def test_admin_can_create_delete_and_mark_statuses(client):
    test_client, admin, _user = client
    headers = auth_headers(admin)

    created = test_client.post(
        "/hardware",
        json={
            "name": "Admin-created laptop",
            "brand": "Framework",
            "purchaseDate": "2026-06-22",
            "status": "Available",
        },
        headers=headers,
    )

    assert created.status_code == 201
    hardware_id = created.json()["id"]

    repair = test_client.post(f"/hardware/{hardware_id}/repair", headers=headers)
    available = test_client.post(f"/hardware/{hardware_id}/available", headers=headers)
    deleted = test_client.delete(f"/hardware/{hardware_id}", headers=headers)

    assert repair.status_code == 200
    assert repair.json()["status"] == "Repair"
    assert available.status_code == 200
    assert available.json()["status"] == "Available"
    assert deleted.status_code == 204
