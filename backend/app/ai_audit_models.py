from typing import Any, Literal

from pydantic import BaseModel, Field


Severity = Literal["high", "medium", "low"]


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
