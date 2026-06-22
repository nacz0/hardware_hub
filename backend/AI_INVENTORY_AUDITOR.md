# AI Inventory Auditor

`POST /ai/audit` is an admin-only MVP-safe AI integration for reviewing current
hardware inventory. The endpoint loads inventory from SQLite, runs
deterministic checks, then optionally asks OpenAI for an advisory structured
report through the official OpenAI Python SDK.

The implementation is split by responsibility:

- `ai_audit.py`: FastAPI route orchestration
- `ai_audit_checks.py`: deterministic inventory checks
- `ai_audit_openai.py`: OpenAI request building, redaction, and fallback logging
- `ai_audit_reports.py`: deterministic and AI report merging
- `ai_audit_models.py`: Pydantic response models and JSON schema

The deterministic checks cover:

- duplicate external IDs
- missing brand
- invalid or missing purchase date, including non-string dirty database values
- future purchase date
- unknown status
- available item with damage-related notes
- in-use item without `assigned_to`

OpenAI usage is read-only. The model receives a minimized inventory view plus
detected facts and returns recommendations in this shape:

```json
{
  "summary": "...",
  "issues": [
    {
      "severity": "high",
      "itemId": 5,
      "title": "...",
      "description": "...",
      "suggestedAction": "..."
    }
  ]
}
```

The backend never lets AI modify inventory records. Deterministic findings are
authoritative: the backend always includes them in the final report, even if
the model omits or rewrites them. AI-only findings are appended as additional
recommendations.

The OpenAI payload redacts raw `assigned_to`, `notes`, and `history` values.
Instead, it sends booleans such as whether an assignee exists and whether
damage-related text was detected.

If `OPENAI_AUDIT_MOCK` is set to `1`, `true`, `yes`, or `on`, if
`OPENAI_API_KEY` is missing, or if the OpenAI request fails, the endpoint
returns deterministic fallback output using the same response model. Tests
should enable mock mode or leave `OPENAI_API_KEY` unset so they never call the
real OpenAI API.

OpenAI request failures and invalid model responses are logged server-side. The
response summary also includes a sanitized fallback reason so admins can tell
when they received a deterministic-only report because the AI path was
unavailable.
