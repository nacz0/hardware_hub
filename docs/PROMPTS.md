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

Summary: Create the FastAPI backend scaffold inside `backend/` only.

Outcome: Added a minimal FastAPI app with SQLite connection helper,
`requirements.txt`, CORS for the local Vue frontend at
`http://localhost:5173`, and `GET /health` returning `{"status": "ok"}`.
Verified the health endpoint with FastAPI's test client.

Correction: moved backend ignore rules from `backend/.gitignore` to the root
`.gitignore` because this project is a monorepo, and documented that decision
in `docs/DECISIONS.md`.

### Prompt

Summary: Implement the backend hardware database model and seed import using
SQLite, while preserving intentionally dirty seed values for later AI auditing.

Outcome: Added a `hardware` table initialized by the FastAPI backend with an
internal database primary key and preserved source identifiers as
`external_id`, allowing duplicate seed IDs to remain visible. Added
`GET /hardware` to return all seeded rows, including invalid dates, unknown
statuses, missing brands, notes, assigned users, and history values. Added a
short code comment explaining that dirty seed data is kept for the auditor.

Correction: moved the hardware seed list out of the database helper into
`backend/app/seed_data.py`, leaving `backend/app/database.py` responsible for
schema creation, idempotent seeding, and hardware reads.

### Prompt

Summary: Implement simple local authentication and authorization inside
`backend/` using bcrypt password hashing, JWT access tokens, admin/user roles,
initial admin seeding from environment variables, and protected auth/admin
endpoints.

Outcome: Added `bcrypt` and `PyJWT` backend dependencies. Added a `users` table
with hashed passwords and roles. Added initial admin seeding, `POST
/auth/login`, `GET /auth/me`, and admin-only `POST /admin/users`. The backend
enforces roles server-side, rejects invalid logins with `401`, requires a
32-byte `JWT_SECRET`, validates emails, caps bcrypt password input length, and
does not promote an existing user during admin seeding.

Correction: refactored user persistence and authentication logic out of
`backend/app/database.py` into `backend/app/users.py`. Verified the admin/user
flow, invalid login, role denial, invalid email, overlong password, JWT secret
startup failures, and non-promoting seed behavior.
