from datetime import date
import json
import logging
import os
import sys
from pathlib import Path

os.environ.setdefault("JWT_SECRET", "test-secret-value-that-is-long-enough")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from fastapi.testclient import TestClient

from app import ai_audit_checks
from app import ai_audit_openai
from app import database
from app.auth import create_access_token
from app.main import app
from app.users import create_user


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_AUDIT_MOCK", raising=False)
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


def test_user_cannot_return_in_use_hardware_without_assignee(client):
    test_client, admin, user = client
    hardware = create_hardware_item(test_client, admin, status="In Use")

    response = test_client.post(
        f"/hardware/{hardware['id']}/return",
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Hardware cannot be returned without an assigned user"


def test_user_can_return_hardware_assigned_to_them(client):
    test_client, admin, user = client
    hardware = create_hardware_item(
        test_client,
        admin,
        status="In Use",
        assigned_to=user["email"],
    )

    response = test_client.post(
        f"/hardware/{hardware['id']}/return",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Available"
    assert response.json()["assigned_to"] is None


def test_user_cannot_return_hardware_assigned_to_someone_else(client):
    test_client, admin, user = client
    hardware = create_hardware_item(
        test_client,
        admin,
        status="In Use",
        assigned_to="other@example.com",
    )

    response = test_client.post(
        f"/hardware/{hardware['id']}/return",
        headers=auth_headers(user),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Hardware can only be returned by the assigned user"

    unchanged = test_client.get("/hardware").json()
    returned_item = next(item for item in unchanged if item["id"] == hardware["id"])
    assert returned_item["status"] == "In Use"
    assert returned_item["assigned_to"] == "other@example.com"


def test_admin_can_return_hardware_assigned_to_someone_else(client):
    test_client, admin, user = client
    hardware = create_hardware_item(
        test_client,
        admin,
        status="In Use",
        assigned_to=user["email"],
    )

    response = test_client.post(
        f"/hardware/{hardware['id']}/return",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Available"
    assert response.json()["assigned_to"] is None


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


def test_ai_audit_returns_deterministic_report_without_openai_key(client):
    test_client, admin, _user = client

    response = test_client.post("/ai/audit", headers=auth_headers(admin))

    assert response.status_code == 200
    report = response.json()
    assert report["summary"]
    assert isinstance(report["issues"], list)

    issue_titles = {issue["title"] for issue in report["issues"]}
    assert "Duplicate external ID" in issue_titles
    assert "Missing brand" in issue_titles
    assert "Invalid or missing purchase date" in issue_titles
    assert "Future purchase date" in issue_titles
    assert "Unknown status" in issue_titles
    assert "Available item has damage-related notes" in issue_titles
    assert "In-use item is unassigned" in issue_titles

    for issue in report["issues"]:
        assert issue["severity"] in {"high", "medium", "low"}
        assert isinstance(issue["itemId"], int)
        assert issue["title"]
        assert issue["description"]
        assert issue["suggestedAction"]


def test_ai_audit_does_not_modify_inventory(client):
    test_client, admin, _user = client
    before = test_client.get("/hardware").json()

    response = test_client.post("/ai/audit", headers=auth_headers(admin))

    assert response.status_code == 200
    assert test_client.get("/hardware").json() == before


def test_ai_audit_requires_admin(client):
    test_client, _admin, user = client

    missing_token_response = test_client.post("/ai/audit")
    user_response = test_client.post(
        "/ai/audit",
        headers=auth_headers(user),
    )

    assert missing_token_response.status_code == 401
    assert user_response.status_code == 403


def test_ai_audit_treats_non_string_purchase_date_as_invalid():
    issues = ai_audit_checks.detect_inventory_facts(
        [
            {
                "id": 99,
                "external_id": 99,
                "name": "Dirty date device",
                "brand": "Test",
                "purchase_date": 20230101,
                "status": "Available",
                "notes": None,
                "assigned_to": None,
                "history": None,
            }
        ],
        today=date(2026, 6, 22),
    )

    assert [issue["title"] for issue in issues] == [
        "Invalid or missing purchase date",
    ]


def test_ai_audit_mock_mode_skips_openai_even_with_api_key(client, monkeypatch):
    test_client, admin, _user = client
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_AUDIT_MOCK", "1")

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("OpenAI API should not be called in mock mode")

    monkeypatch.setattr(ai_audit_openai, "OpenAI", fail_if_called)

    response = test_client.post("/ai/audit", headers=auth_headers(admin))

    assert response.status_code == 200
    assert response.json()["issues"]


def test_ai_audit_logs_and_reports_openai_fallback(client, monkeypatch, caplog):
    test_client, admin, _user = client
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    caplog.set_level(logging.WARNING, logger=ai_audit_openai.__name__)

    class FakeResponse:
        output_text = "not-json"

    class FakeResponses:
        def create(self, **_kwargs):
            return FakeResponse()

    class FakeOpenAI:
        def __init__(self, **_kwargs):
            self.responses = FakeResponses()

    monkeypatch.setattr(ai_audit_openai, "OpenAI", FakeOpenAI)

    response = test_client.post("/ai/audit", headers=auth_headers(admin))

    assert response.status_code == 200
    assert (
        "AI audit unavailable: OpenAI returned an invalid structured report."
        in response.json()["summary"]
    )
    assert "OpenAI inventory audit returned an invalid structured report" in caplog.text


def test_ai_audit_uses_openai_sdk_when_api_key_is_set(client, monkeypatch):
    test_client, admin, _user = client
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    calls = []

    class FakeResponse:
        output_text = (
            '{"summary":"AI reviewed deterministic findings.",'
            '"issues":[{"severity":"low","itemId":1,"title":"Review item",'
            '"description":"AI advisory recommendation.",'
            '"suggestedAction":"Review the record."}]}'
        )

    class FakeResponses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return FakeResponse()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            calls.append(kwargs)
            self.responses = FakeResponses()

    monkeypatch.setattr(ai_audit_openai, "OpenAI", FakeOpenAI)

    response = test_client.post("/ai/audit", headers=auth_headers(admin))

    assert response.status_code == 200
    report = response.json()
    assert "AI reviewed deterministic findings." in report["summary"]
    issue_titles = {issue["title"] for issue in report["issues"]}
    assert "Duplicate external ID" in issue_titles
    assert "Review item" in issue_titles
    assert calls[0] == {"api_key": "test-key", "timeout": 20.0}
    assert calls[1]["model"] == "gpt-4.1-mini"
    assert calls[1]["text"]["format"]["type"] == "json_schema"
    assert calls[1]["text"]["format"]["strict"] is True

    payload = json.loads(calls[1]["input"][1]["content"])
    encoded_payload = calls[1]["input"][1]["content"]
    assert "j.doe@booksy.com" not in encoded_payload
    assert "Battery swelling, do not issue without service." not in encoded_payload
    assert "Returned by user with liquid damage. Keyboard sticky." not in encoded_payload

    for item in payload["inventory"]:
        assert "assigned_to" not in item
        assert "notes" not in item
        assert "history" not in item
        assert "assigned_to_present" in item
        assert "notes_present" in item
        assert "history_present" in item
        assert "damage_related_text_detected" in item
