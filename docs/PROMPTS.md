# Prompt Trail

Concise prompt history for review. Do not paste assignment content verbatim.

## Architecture Planning

Requested a 4-5 hour MVP plan for Hardware Hub using FastAPI, SQLite, Vue 3,
OpenAI API, GitHub Actions, Vercel, and Railway if time allows.

Required features: admin-created users, login, hardware management, user
management, dashboard sorting/filtering, rent/return flow, Inventory Auditor,
critical tests, and README documentation.

## Codex Outcome

Codex produced the first plan, API outline, schema proposal, test list,
shortcuts, and README risk notes.

Issue: the first version introduced generic inventory fields/statuses that were
not in the assignment.

## Manual Corrections

- Use `name`, `brand`, `purchaseDate`, `status`, `notes`, `assignedTo`,
  `history`.
- Preserve `Available`, `In Use`, `Repair`.
- Do not make category/condition/rented/maintenance/retired core fields.
- Dashboard shows Name, Brand, Purchase Date, Status.
- Access requires an admin-created account.
- AI-native feature is Inventory Auditor.
- Dirty seed data should be preserved and audited.

## Documentation Condensing

Docs were shortened to early-stage scaffolds so they stay review-friendly and
can grow with implementation evidence.

## Future Prompts

### Prompt

Date: 2026-06-22

Summary: Create the FastAPI backend scaffold inside `backend/` only.

Outcome: Added a minimal FastAPI app with SQLite connection helper,
`requirements.txt`, CORS for the local Vue frontend at
`http://localhost:5173`, and `GET /health` returning `{"status": "ok"}`.
Verified the health endpoint with FastAPI's test client.

Correction: moved backend ignore rules from `backend/.gitignore` to the root
`.gitignore` because this project is a monorepo, and documented that decision
in `docs/DECISIONS.md`.
