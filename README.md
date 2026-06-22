# Hardware Hub

Internal hardware rental MVP for a recruitment assignment.

## Project Overview

Hardware Hub lets admins manage hardware and local user accounts, while users
log in to view, rent, and return hardware.

The assignment hardware fields are the source of truth:

- `name`
- `brand`
- `purchaseDate`
- `status`
- `notes`
- `assignedTo`
- `history`

Preserved status values: `Available`, `In Use`, `Repair`.

## Tech Stack

- Backend: FastAPI
- Frontend: Vue 3 + TypeScript
- Database: SQLite
- AI: OpenAI API
- CI: GitHub Actions
- Deployment targets: Vercel frontend, Railway backend if time allows

## MVP Scope

- Admin-created user accounts only
- Login-protected app access
- Admin hardware management
- Admin user management
- Hardware dashboard with sorting/filtering
- Dashboard columns: Name, Brand, Purchase Date, Status
- Rent/return flow with business guards
- Inventory Auditor as the AI-native feature
- At least 3 critical tests

Out of scope for core MVP: category, condition, rented, maintenance, retired.
These can be future improvements, but they are not assignment fields.

## Features Planned/Implemented

| Feature | Status |
| --- | --- |
| Documentation baseline | Implemented |
| Backend API | Planned |
| SQLite schema and seed import | Planned |
| Login and role guards | Planned |
| Admin hardware/user management | Planned |
| Dashboard sorting/filtering | Planned |
| Rent/return flow | Planned |
| Inventory Auditor | Planned |
| Critical tests | Planned |
| GitHub Actions CI | Planned |

## Local Setup

Placeholder until the app is scaffolded.

```bash
# backend
pytest
uvicorn app.main:app --reload

# frontend
npm install
npm run dev
```

## Environment Variables

Placeholder until implementation.

```bash
DATABASE_URL=sqlite:///./hardware_hub.db
JWT_SECRET=replace-me
OPENAI_API_KEY=optional-locally
OPENAI_MODEL=gpt-4.1-mini
```

## Testing

Placeholder until implementation.

Expected coverage:

- Auth and admin role guards
- Rent/return business rules
- Inventory Auditor access and failure handling

## Implementation Status

### Fully Implemented

- Initial documentation files
- Corrected assignment-aligned scope

### Shortcuts & Hacks

- SQLite for speed
- Simple JWT auth without refresh tokens
- Admin-created accounts only
- Dirty seed data preserved and flagged
- Table-first UI
- Backend does not currently expose a user-list endpoint, so the frontend only
  shows user accounts created during the current admin session.

### Partial/Missing

- Backend, frontend, tests, CI, deployment config
- OpenAI-backed Inventory Auditor endpoint

### Next 24h Roadmap

1. Scaffold FastAPI and Vue.
2. Add SQLite schema and seed import.
3. Implement auth, admin users, and hardware CRUD.
4. Build dashboard and rent/return flow.
5. Add deterministic audit checks plus OpenAI summary.
6. Add critical tests and CI.

## AI-Native Layer

Inventory Auditor runs deterministic checks first, then uses the OpenAI API to
summarize risks and suggested admin actions.

Initial checks should include duplicate source IDs, invalid dates, missing
brands, invalid statuses, damage notes on available items, and `In Use` items
without `assignedTo`.

AI output is advisory only and must not automatically mutate inventory records.

## Security and Deployment Notes

This MVP is not production-ready.

- Passwords must be hashed.
- Admin checks must run server-side.
- `OPENAI_API_KEY` must stay backend-only.
- Rate limiting, password reset, refresh tokens, and audit logging are deferred.
- SQLite is acceptable for the assignment MVP; production should use Postgres.
