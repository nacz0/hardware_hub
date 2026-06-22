from datetime import date
import re
from typing import Any

from app.ai_audit_models import build_issue


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
