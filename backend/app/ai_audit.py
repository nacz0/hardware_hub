from fastapi import APIRouter, Depends

from app.ai_audit_checks import detect_inventory_facts
from app.ai_audit_models import AuditReport
from app.ai_audit_openai import call_openai_audit
from app.ai_audit_reports import deterministic_audit_report, merge_ai_report
from app.auth import require_admin
from app.database import list_hardware


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/audit", response_model=AuditReport)
def audit_inventory(_admin: dict = Depends(require_admin)) -> dict:
    inventory = list_hardware()
    facts = detect_inventory_facts(inventory)
    ai_report, fallback_reason = call_openai_audit(inventory, facts)
    if ai_report is not None:
        return merge_ai_report(ai_report, facts)

    return deterministic_audit_report(facts, fallback_reason=fallback_reason)
