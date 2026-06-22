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
| Backend API | Implemented |
| SQLite schema and seed import | Implemented |
| Login and role guards | Implemented |
| Admin hardware/user management | Implemented |
| Dashboard sorting/filtering | Implemented |
| Rent/return flow | Implemented |
| Inventory Auditor | Implemented |
| Figma-inspired frontend shell | Implemented |
| Critical tests | Implemented |
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
- Rent/return business rules, including rejecting unassigned `In Use` returns
- Inventory Auditor access and failure handling

## Implementation Status

### Fully Implemented

- Initial documentation files
- Corrected assignment-aligned scope
- FastAPI backend with auth, role guards, hardware routes, and AI audit route
- SQLite schema and dirty seed import
- Vue frontend login, table-first hardware dashboard, admin tools, and AI audit view
- Figma-inspired frontend shell with standalone login, sidebar navigation, and
  compact table/status styling
- Strict purchase-date dashboard sorting that keeps invalid/missing dirty dates
  visible but ordered after valid ISO dates
- Rent/return guards that prevent returning `In Use` hardware without an
  assignee

### Shortcuts & Hacks

- SQLite for speed
- Simple JWT auth without refresh tokens
- Admin-created accounts only
- Dirty seed data preserved and flagged
- Table-first UI
- Frontend uses simple local state for navigation instead of Vue Router.
- The Figma MCP file was not directly inspectable without edit access, so the
  published Figma site was reviewed with the Chrome-backed browser MCP.
- The API health check remains in the UI but is visually de-emphasized below
  the main work area.
- Backend does not currently expose a user-list endpoint, so the frontend only
  shows user accounts created during the current admin session.

### Partial/Missing

- CI and deployment config
- Separate My Rentals screen from the Figma mock
- Add/edit device modal polish from the Figma mock

### Next 24h Roadmap

1. Add GitHub Actions for backend tests and frontend build.
2. Add deployment configuration if needed.
3. Decide whether to implement the Figma `My Rentals` screen.
4. Decide whether admin add/edit should move into modal-style flows.
5. Add final browser smoke checks before submission.

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
