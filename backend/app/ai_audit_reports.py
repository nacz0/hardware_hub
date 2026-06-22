from typing import Any

from app.ai_audit_models import AuditReport


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
