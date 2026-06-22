# Hardware Hub

Internal hardware rental MVP for a recruitment assignment. The app lets admins
manage hardware and local user accounts, while users sign in to view, rent, and
return available hardware.

This is an honest MVP, not a production-ready asset system.

## Live Deployment

- Frontend: https://hardware-hub-ten.vercel.app/
- Backend: https://hardwarehub-production-a77c.up.railway.app/
- Backend health check: https://hardwarehub-production-a77c.up.railway.app/health

## More Documentation

Additional project documentation lives in `docs/`:

- `docs/AI_LOG.md`: AI usage, Figma/Chrome MCP notes, OpenAI API usage, manual
  review, and data strategy.
- `docs/PROMPTS.md`: concise record of the most important prompts and outcomes.
- `docs/DECISIONS.md`: architecture decisions and MVP trade-offs.

## Project Overview

Hardware Hub tracks assignment-defined hardware records and keeps the original
dirty dataset visible for auditing instead of silently cleaning it.

The hardware model follows the assignment fields:

- `name`
- `brand`
- `purchaseDate`
- `status`
- `notes`
- `assignedTo`
- `history`

The preserved status values are `Available`, `In Use`, and `Repair`. Dirty
values such as missing brands, invalid dates, duplicate source IDs, future
purchase dates, and `Unknown` status are intentionally retained so the audit
feature can report them.

## Tech Stack

- Backend: Python, FastAPI, Pydantic, SQLite, bcrypt, PyJWT
- Frontend: Vue 3, TypeScript, Vite
- AI integration: OpenAI Python SDK using the Responses API
- Tests: pytest for backend business rules, `vue-tsc` and Vite production build
- CI: GitHub Actions for backend tests and frontend build
- Deployment config: Railway backend, Vercel frontend

## Features Implemented

- Login with JWT access tokens and server-side current-user lookup
- Bcrypt password hashing for stored user passwords
- Admin-created user accounts with `admin` and `user` roles
- Server-side admin guards for admin-only routes
- Hardware list API seeded from the assignment dataset
- User dashboard with search, status filter, brand filter, name sorting, and
  strict purchase-date sorting
- Rent flow for `Available` hardware
- Return flow with ownership rules: regular users can return their own assigned
  hardware, admins can return any assigned `In Use` hardware
- Admin panel for creating users, adding hardware, marking hardware as repair,
  deleting hardware, and refreshing records
- Admin-only AI Inventory Auditor
- Deterministic audit checks for duplicate IDs, missing brands, invalid dates,
  future dates, unknown statuses, damage notes on available items, and unassigned
  `In Use` items
- OpenAI-backed advisory audit summary with deterministic fallback
- Frontend shell inspired by the Figma mock: standalone login, sidebar
  navigation, table-first work area, and compact status badges
- GitHub Actions CI for backend tests and frontend build

## Setup Instructions

Prerequisites:

- Python 3.12 recommended
- Node.js 22 recommended
- npm

Create a local `.env` file in the repository root or in `backend/`. The backend
loads both locations and does not require a committed `.env`.

```powershell
Copy-Item .env.example .env
```

Edit `.env` before starting the backend. At minimum, set a strong
`JWT_SECRET`. Set `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` if you want
the app to seed the first admin account automatically.

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Default local URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`

The SQLite database is created automatically at `backend/hardware_hub.db` when
the backend initializes.

## Test Instructions

Backend tests:

```powershell
cd backend
$env:JWT_SECRET = "test-secret-value-that-is-long-enough"
$env:OPENAI_AUDIT_MOCK = "1"
pytest
```

Frontend production build:

```powershell
cd frontend
npm ci
npm run build
```

CI runs the same core checks through `.github/workflows/ci.yml`:

- Backend job: installs `backend/requirements.txt` and runs `pytest`
- Frontend job: installs with `npm ci` and runs `npm run build`

The latest documented local verification before this final documentation pass
was 17 passing backend tests and a successful frontend production build.

## Deployment Instructions

### Backend on Railway

Create a Railway service from the repository and set the service root directory
to `backend`. The checked-in `backend/railway.json` uses Railpack, starts the API
with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

It also configures `/health` as the health check.

Set Railway environment variables:

```bash
JWT_SECRET=replace-with-at-least-32-random-bytes
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=replace-with-a-strong-password
FRONTEND_URL=https://hardware-hub-ten.vercel.app
OPENAI_API_KEY=optional-for-inventory-auditor
OPENAI_MODEL=gpt-4.1-mini
```

Railway provides `PORT`; do not set it manually.

Important deployment caveat: the current backend uses SQLite at
`backend/hardware_hub.db`. Treat Railway deployment as demo-grade unless
persistent storage or Postgres support is added.

### Frontend on Vercel

Create a Vercel project from the repository root. The checked-in `vercel.json`
installs dependencies under `frontend/`, builds the Vite app, and serves
`frontend/dist`.

Set this Vercel environment variable:

```bash
VITE_API_URL=https://hardwarehub-production-a77c.up.railway.app
```

After Vercel gives you the production frontend URL, set that URL as
`FRONTEND_URL` on Railway so CORS allows browser requests.

## Environment Variables

| Variable | Used by | Required | Purpose |
| --- | --- | --- | --- |
| `JWT_SECRET` | Backend | Yes | HS256 JWT signing secret. Must be at least 32 bytes. |
| `INITIAL_ADMIN_EMAIL` | Backend | No, but useful | Seeds the first admin if no admin exists. |
| `INITIAL_ADMIN_PASSWORD` | Backend | No, but useful | Password for the seeded admin. |
| `FRONTEND_URL` | Backend | Deployment | Comma-separated CORS allowlist. Defaults locally to `http://localhost:5173`. |
| `OPENAI_API_KEY` | Backend | No | Enables OpenAI-backed audit summaries. If absent, deterministic audit fallback is used. |
| `OPENAI_MODEL` | Backend | No | Defaults to `gpt-4.1-mini` in code. |
| `OPENAI_AUDIT_MOCK` | Backend | No | When truthy, skips OpenAI calls and returns deterministic audit output. Used by tests/CI. |
| `VITE_API_URL` | Frontend | Deployment | Backend base URL baked into the Vite frontend build. Defaults locally to `http://127.0.0.1:8000`. |
| `ALLOWED_EMAIL_DOMAIN` | Example only | No | Present in `.env.example`, but not enforced by the current backend. |

## Implementation Status

### Fully Implemented

- FastAPI backend with health, auth, user, hardware, and AI audit routes
- SQLite schema initialization and idempotent dirty seed import
- Password hashing, JWT login, current-user endpoint, and role dependencies
- Admin-only user creation
- Hardware create, list, delete, repair, rent, and return actions
- Return authorization for assigned users and admins
- Vue login, session restore, role-gated navigation, dashboard, admin panel, and
  AI auditor view
- Search, filtering, sorting, status counts, loading states, and API error
  display in the frontend
- Deterministic inventory audit plus optional OpenAI structured report
- Redaction of raw assignee, notes, and history values before sending audit
  context to OpenAI
- Backend pytest coverage for critical auth, rental, return, and AI auditor
  behavior
- Frontend TypeScript/Vite build
- GitHub Actions CI
- Vercel and Railway deployment configuration

### Shortcuts and Hacks

| Shortcut or hack | Why it was acceptable for the MVP | Future production refactor |
| --- | --- | --- |
| SQLite database | Fast local setup and simple assignment review. | Move to Postgres, add migrations, backups, and environment-specific database URLs. |
| No ORM or repository layer | Direct SQLite functions kept the backend small. | Add a persistence layer with transaction boundaries and typed data access. |
| JWT access token only | Quick auth path for a small internal tool. | Add refresh tokens or server-side sessions, revocation, rotation, and shorter-lived access tokens. |
| Token stored in `localStorage` | Simple Vue integration. | Prefer hardened session cookies or a reviewed token storage strategy with stronger XSS controls. |
| Admin-created accounts only | Matches the internal-tool premise. | Add invite flows, password reset, account disablement, and user listing/editing. |
| Admin panel only lists users created during the current browser session | Backend has `POST /admin/users` but no `GET /admin/users`. | Add audited user management endpoints and a persisted admin user table view. |
| State-based view switching instead of Vue Router | Enough for three MVP screens. | Introduce Vue Router, route guards, and deep links. |
| Browser `window.confirm` for deletion | Minimal confirmation behavior. | Replace with an accessible modal and clearer destructive-action affordances. |
| Dirty seed data preserved as-is | The assignment dataset includes data-quality issues. | Keep raw imports, but add a reviewed correction workflow and source-of-truth import history. |
| OpenAI audit is advisory and fallback-first | Avoids making business state depend on LLM availability. | Add saved audit reports, prompt/version tracking, and admin acknowledgement workflows. |
| Railway + SQLite deployment | Good enough to demonstrate the app. | Use persistent managed storage before treating deployment as durable. |

### Partial/Missing

- Production-grade authentication hardening: refresh/revocation, rate limiting,
  password reset, account lockout, and full audit logging
- Persistent production database and migration tooling
- Full admin user list/edit/deactivate workflow
- Hardware edit workflow beyond add/delete/repair
- Dedicated "My Rentals" screen from the Figma mock
- End-to-end browser tests committed to the repo
- Observability: structured logs, metrics, tracing, and alerting
- Real asset import pipeline beyond the static seed list
- Semantic search or general chat assistant features
- Formal accessibility and security review

### Next 24h Roadmap

1. Add `GET /admin/users` and display persisted users in the admin panel.
2. Add hardware edit support for correcting dirty records without deleting them.
3. Add Playwright smoke tests for login, rent, return ownership, admin add, and
   AI audit fallback.
4. Replace SQLite with Postgres or at least introduce a database URL abstraction
   and migration plan.
5. Tighten deployment verification: production env checklist, seeded admin
   rotation, and CORS validation after every deploy.

## AI-Native Layer Explanation

The AI-native layer is the Inventory Auditor. It is intentionally built as an
admin-only, read-only workflow:

1. The backend loads current inventory from SQLite.
2. Deterministic Python checks detect known data-quality and workflow risks.
3. If `OPENAI_API_KEY` is configured and mock mode is off, the backend sends a
   minimized, redacted inventory view plus deterministic findings to OpenAI.
4. OpenAI returns a structured JSON audit summary and issue list.
5. The backend validates the model response and merges it with deterministic
   findings.
6. If OpenAI is unavailable, missing, or returns invalid structure, the endpoint
   returns deterministic fallback output using the same response model.

The frontend never calls OpenAI directly and never receives the API key. AI
output is advisory only; it cannot mutate inventory records.

## Security Notes

This MVP has useful security foundations, but it is not production-ready.

- Passwords are bcrypt-hashed and capped to bcrypt's 72-byte limit.
- Admin checks run server-side, not only in the frontend.
- `JWT_SECRET`, initial admin credentials, and `OPENAI_API_KEY` must stay in
  environment variables and out of git.
- `OPENAI_API_KEY` is backend-only; the frontend only calls the Hardware Hub API.
- Raw assignee, notes, and history fields are redacted from the OpenAI audit
  payload.
- JWTs are stored in `localStorage`, which is acceptable for this MVP but should
  be revisited for production because XSS would expose tokens.
- There is no rate limiting, refresh token flow, token revocation, password
  reset, account lockout, or complete audit log.
- CORS is environment-driven, but production URLs must be configured carefully.
- SQLite deployment should not be treated as durable production storage.
- LLM output is treated as untrusted advisory text and is validated against a
  schema before display.
