from __future__ import annotations

from datetime import date
import json
import logging
import os
import re
from typing import Any, Literal

from fastapi import APIRouter, Depends
from openai import APIError, OpenAI
from pydantic import BaseModel, Field, ValidationError

from app.auth import require_admin
from app.database import list_hardware


Severity = Literal["high", "medium", "low"]

VALID_STATUSES = {"Available", "In Use", "Repair"}
DAMAGE_RELATED_TERMS = (
    "battery swelling",
    "broken",
    "crack",
    "cracked",
    "damage",
    "damaged",
    "defect",
    "defective",
    "liquid",
    "service",
    "sticky",
    "swelling",
)
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class AuditIssue(BaseModel):
    severity: Severity
    itemId: int
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    suggestedAction: str = Field(min_length=1)


class AuditReport(BaseModel):
    summary: str = Field(min_length=1)
    issues: list[AuditIssue]


AUDIT_REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "issues"],
    "properties": {
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "severity",
                    "itemId",
                    "title",
                    "description",
                    "suggestedAction",
                ],
                "properties": {
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "itemId": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "suggestedAction": {"type": "string"},
                },
            },
        },
    },
}


def build_issue(
    *,
    severity: Severity,
    item_id: int,
    title: str,
    description: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "itemId": item_id,
        "title": title,
        "description": description,
        "suggestedAction": suggested_action,
    }


def parse_purchase_date(value: Any) -> tuple[date | None, bool]:
    if value is None:
        return None, False

    if not isinstance(value, str):
        return None, False

    if not value.strip():
        return None, False

    normalized = value.strip()
    if not ISO_DATE_PATTERN.fullmatch(normalized):
        return None, False

    try:
        return date.fromisoformat(normalized), True
    except ValueError:
        return None, False


def has_damage_related_text(item: dict[str, Any]) -> bool:
    text = " ".join(
        str(item.get(field) or "") for field in ("notes", "history")
    ).lower()
    return any(term in text for term in DAMAGE_RELATED_TERMS)


def detect_inventory_facts(
    inventory: list[dict[str, Any]],
    *,
    today: date | None = None,
) -> list[dict[str, Any]]:
    today = today or date.today()
    issues: list[dict[str, Any]] = []
    external_id_groups: dict[Any, list[dict[str, Any]]] = {}

    for item in inventory:
        external_id = item.get("external_id")
        if external_id is not None:
            external_id_groups.setdefault(external_id, []).append(item)

    for external_id, items in external_id_groups.items():
        if len(items) < 2:
            continue

        item_ids = ", ".join(str(item["id"]) for item in items)
        for item in items:
            issues.append(
                build_issue(
                    severity="high",
                    item_id=item["id"],
                    title="Duplicate external ID",
                    description=(
                        f"External ID {external_id} is shared by hardware "
                        f"records {item_ids}."
                    ),
                    suggested_action=(
                        "Confirm the source system ID and correct one of the records."
                    ),
                )
            )

    for item in inventory:
        item_id = item["id"]
        brand = item.get("brand")
        purchase_date_value = item.get("purchase_date")
        status = item.get("status")

        if brand is None or not str(brand).strip():
            issues.append(
                build_issue(
                    severity="medium",
                    item_id=item_id,
                    title="Missing brand",
                    description="Brand is empty, so the item is harder to identify.",
                    suggested_action="Fill in the manufacturer or normalize the record.",
                )
            )

        parsed_purchase_date, valid_purchase_date = parse_purchase_date(
            purchase_date_value
        )
        if not valid_purchase_date:
            issues.append(
                build_issue(
                    severity="medium",
                    item_id=item_id,
                    title="Invalid or missing purchase date",
                    description=(
                        "Purchase date must be present in YYYY-MM-DD format."
                    ),
                    suggested_action=(
                        "Validate the original purchase record and enter an ISO date."
                    ),
                )
            )
        elif parsed_purchase_date is not None and parsed_purchase_date > today:
            issues.append(
                build_issue(
                    severity="high",
                    item_id=item_id,
                    title="Future purchase date",
                    description=(
                        f"Purchase date {purchase_date_value} is after {today.isoformat()}."
                    ),
                    suggested_action=(
                        "Correct the purchase date before using it for reporting."
                    ),
                )
            )

        if status not in VALID_STATUSES:
            issues.append(
                build_issue(
                    severity="medium",
                    item_id=item_id,
                    title="Unknown status",
                    description=(
                        f"Status {status!r} is not one of "
                        "Available, In Use, or Repair."
                    ),
                    suggested_action=(
                        "Move the item to a supported status after confirming its state."
                    ),
                )
            )

        if status == "Available" and has_damage_related_text(item):
            issues.append(
                build_issue(
                    severity="high",
                    item_id=item_id,
                    title="Available item has damage-related notes",
                    description=(
                        "The item is marked Available but notes or history mention damage."
                    ),
                    suggested_action=(
                        "Review the item condition and move it to Repair if needed."
                    ),
                )
            )

        if status == "In Use" and not str(item.get("assigned_to") or "").strip():
            issues.append(
                build_issue(
                    severity="high",
                    item_id=item_id,
                    title="In-use item is unassigned",
                    description="The item is marked In Use without an assigned user.",
                    suggested_action=(
                        "Assign the current user or return the item to Available."
                    ),
                )
            )

    return issues


def deterministic_audit_report(
    issues: list[dict[str, Any]],
    *,
    fallback_reason: str | None = None,
) -> dict[str, Any]:
    summary = deterministic_summary(issues)
    if fallback_reason is not None:
        summary = f"{summary} AI audit unavailable: {fallback_reason}."

    return AuditReport(
        summary=summary,
        issues=issues,
    ).model_dump()


def deterministic_summary(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "No deterministic inventory issues were detected."

    return (
        f"Deterministic inventory audit found {len(issues)} issue"
        f"{'' if len(issues) == 1 else 's'} requiring review."
    )


def minimize_inventory_for_ai(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "external_id": item.get("external_id"),
            "name": item.get("name"),
            "brand": item.get("brand"),
            "purchase_date": item.get("purchase_date"),
            "status": item.get("status"),
            "assigned_to_present": bool(str(item.get("assigned_to") or "").strip()),
            "notes_present": bool(str(item.get("notes") or "").strip()),
            "history_present": bool(str(item.get("history") or "").strip()),
            "damage_related_text_detected": has_damage_related_text(item),
        }
        for item in inventory
    ]


def issue_key(issue: dict[str, Any]) -> tuple[int, str]:
    return issue["itemId"], issue["title"]


def merge_ai_report(
    ai_report: dict[str, Any],
    deterministic_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    deterministic_keys = {issue_key(issue) for issue in deterministic_issues}
    merged_issues = list(deterministic_issues)

    for issue in ai_report["issues"]:
        if issue_key(issue) not in deterministic_keys:
            merged_issues.append(issue)

    ai_summary = ai_report["summary"].strip()
    if deterministic_issues:
        summary = f"{deterministic_summary(deterministic_issues)} AI summary: {ai_summary}"
    else:
        summary = ai_summary

    return AuditReport(summary=summary, issues=merged_issues).model_dump()


def build_openai_request(
    inventory: list[dict[str, Any]],
    facts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "input": [
            {
                "role": "system",
                "content": (
                    "You are an inventory audit assistant. Return only the "
                    "structured JSON report requested by the schema. Include every "
                    "deterministic finding provided by the application, and you may "
                    "add advisory recommendations. You must not request or imply any "
                    "database writes."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "inventory": inventory,
                        "detectedFacts": facts,
                        "requirements": {
                            "advisoryOnly": True,
                            "databaseMutationAllowed": False,
                            "deterministicFactsAreAuthoritative": True,
                            "sensitiveFieldsRedacted": [
                                "assigned_to",
                                "notes",
                                "history",
                            ],
                        },
                    },
                    ensure_ascii=True,
                ),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "inventory_audit_report",
                "strict": True,
                "schema": AUDIT_REPORT_SCHEMA,
            }
        },
    }


def extract_response_text(response: Any) -> str | None:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str):
        return output_text

    chunks: list[str] = []
    for output_item in getattr(response, "output", []) or []:
        for content_item in getattr(output_item, "content", []) or []:
            text_value = getattr(content_item, "text", None)
            if isinstance(text_value, str):
                chunks.append(text_value)

    return "".join(chunks) if chunks else None


def openai_audit_mock_enabled() -> bool:
    value = os.getenv("OPENAI_AUDIT_MOCK", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def call_openai_audit(
    inventory: list[dict[str, Any]],
    facts: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    if openai_audit_mock_enabled():
        return None, None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, None

    try:
        client = OpenAI(api_key=api_key, timeout=20.0)
        response = client.responses.create(
            **build_openai_request(minimize_inventory_for_ai(inventory), facts)
        )
        response_text = extract_response_text(response)
        if response_text is None:
            logger.warning(
                "OpenAI inventory audit returned no response text; "
                "using deterministic fallback."
            )
            return None, "OpenAI returned no structured report"

        report = AuditReport.model_validate(json.loads(response_text))
        return report.model_dump(), None
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
        logger.warning(
            "OpenAI inventory audit returned an invalid structured report; "
            "using deterministic fallback.",
            exc_info=True,
        )
        return None, "OpenAI returned an invalid structured report"
    except (
        APIError,
    ):
        logger.warning(
            "OpenAI inventory audit request failed; using deterministic fallback.",
            exc_info=True,
        )
        return None, "OpenAI request failed"


@router.post("/audit", response_model=AuditReport)
def audit_inventory(_admin: dict = Depends(require_admin)) -> dict[str, Any]:
    inventory = list_hardware()
    facts = detect_inventory_facts(inventory)
    ai_report, fallback_reason = call_openai_audit(inventory, facts)
    if ai_report is not None:
        return merge_ai_report(ai_report, facts)

    return deterministic_audit_report(facts, fallback_reason=fallback_reason)
