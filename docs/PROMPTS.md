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

### Prompt

Summary: Implement backend hardware rental and return business logic inside
`backend/`.

Outcome: Added server-side endpoints for renting, returning, marking repair,
marking available, creating hardware, and deleting hardware. Rental is allowed
only from `Available`, return is allowed only from `In Use`, rent assigns the
current user's email, and return clears assignment. Admin-only actions are
guarded on the backend, invalid transitions return `400`, missing permissions
return `403`, and missing hardware returns `404`. Added focused FastAPI tests
for the core business rules and added test dependencies.

Correction: tightened rent/return mutations to use conditional status updates
so the expected source status is enforced at database update time, not only by
an earlier route check.

### Prompt

Summary: Refactor the hardware rental and return implementation so `main.py`
stays small and future updates have clear module ownership.

Outcome: Moved JWT token creation, current-user lookup, and admin dependency
logic into `backend/app/auth.py`. Moved hardware request models, routes, and
business operations into `backend/app/hardware.py`, then registered the router
from `main.py`. `main.py` now focuses on FastAPI app setup, health, login,
current-user, and admin user creation endpoints. Updated tests to import token
creation from the auth module.

Correction: documented the convention in `docs/DECISIONS.md`: keep `main.py`
tidy and split routes, auth, and business logic into focused modules when
behavior grows.

### Prompt

Summary: Add critical backend pytest coverage for hardware rental rules and
admin-only user creation.

Outcome: Reworked `backend/tests/test_hardware_business.py` into six focused
API-level tests covering repair/in-use/available rental behavior, invalid
returns, regular-user denial for user creation, and admin user creation.
Tests use a temporary SQLite database via `tmp_path`, create their own admin
and regular user fixtures, avoid OpenAI API calls, and do not depend on the
developer's local database or fixed seed rows.

Verification: ran `pytest backend\tests`; all six tests passed.

### Prompt

Summary: Implement the backend AI Inventory Auditor feature.

Outcome: Added admin-only `POST /ai/audit`. It loads inventory, runs
deterministic data-quality checks, optionally calls OpenAI through the official
Python SDK, and returns an advisory structured report without mutating records.

Necessary corrections:

- Use the OpenAI SDK, not raw HTTP.
- Keep deterministic findings authoritative and redact sensitive inventory
  fields before sending data to OpenAI.
- Require admin access, handle dirty date values safely, and surface/log
  deterministic fallback when OpenAI is unavailable.
- Split the long auditor file into route, checks, OpenAI, report, and schema
  modules.

Verification: ran `pytest` from `backend/`; all 13 tests passed.

### Prompt

Summary: Create the Vue 3 + TypeScript frontend scaffold inside `frontend/`
using Vite.

Outcome: Added a Vite-powered Vue 3 app with TypeScript configuration,
frontend-local environment files, simple state-based view switching, and the
requested `LoginView`, `DashboardView`, `AdminView`, and `AiAuditorView`.
Added a maintainable CSS baseline and a `GET /health` check wired through
`VITE_API_URL`.

Verification: ran `npm.cmd run build`; the Vue type check and Vite production
build passed. Started the frontend locally and confirmed
`http://localhost:5173/` returned `200`.

### Prompt

Summary: Implement frontend login and the hardware dashboard.

Outcome: Added a typed API client using `VITE_API_URL`, JWT storage in
`localStorage`, session restore with current user role, and a working login
screen. Replaced the placeholder dashboard with hardware loading, status/brand
and text filters, name/purchase-date sorting, displayed assignment fields, and
rent/return buttons that call the backend and refresh the list.

Verification: ran `npm run build`, checked the running backend API, verified
admin and regular user login, exercised hardware list loading, filters,
sorting, and a rent/return flow through the UI.
