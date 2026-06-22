import json
import logging
import os
from typing import Any

from openai import APIError, OpenAI
from pydantic import ValidationError

from app.ai_audit_checks import has_damage_related_text
from app.ai_audit_models import AUDIT_REPORT_SCHEMA, AuditReport
from app.env import load_environment


logger = logging.getLogger(__name__)


load_environment()


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
    except APIError:
        logger.warning(
            "OpenAI inventory audit request failed; using deterministic fallback.",
            exc_info=True,
        )
        return None, "OpenAI request failed"
