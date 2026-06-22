# Prompt Trail

This file records the most important prompts and outcomes. It intentionally does
not include the full chat history.

## 1. MVP Planning

Prompt summary: Plan a 4-5 hour Hardware Hub MVP using FastAPI, SQLite, Vue 3,
OpenAI API, GitHub Actions, Vercel, and Railway if time allows.

Outcome: Created the initial architecture, API outline, test list, scope
trade-offs, and README risk notes.

Correction: The first AI plan introduced generic inventory fields. Manual review
corrected the domain back to the assignment fields and statuses.

## 2. Backend Scaffold

Prompt summary: Create the FastAPI backend scaffold inside `backend/`.

Outcome: Added FastAPI app setup, CORS for local Vue development,
`requirements.txt`, SQLite connection helper, and `GET /health`.

Correction: Moved ignore rules to the root `.gitignore` because this is a
monorepo.

## 3. Hardware Model and Dirty Seed Import

Prompt summary: Implement the backend hardware database model and seed import
while preserving intentionally dirty seed values for AI auditing.

Outcome: Added the `hardware` table, `external_id` source identifier, idempotent
seed import, and `GET /hardware`.

Correction: Moved seed data into `backend/app/seed_data.py` so database setup
and source data had separate ownership.

## 4. Authentication and Authorization

Prompt summary: Implement local auth with bcrypt password hashing, JWT access
tokens, admin/user roles, initial admin seeding from environment variables, and
protected endpoints.

Outcome: Added login, current-user lookup, admin-only user creation, email
normalization, bcrypt password constraints, and JWT secret validation.

Correction: Split auth and user persistence into focused modules instead of
leaving everything in `database.py`.

## 5. Hardware Rental Business Rules

Prompt summary: Implement backend hardware rental and return logic.

Outcome: Added rent, return, repair, available, create, and delete operations.
Rental is allowed only from `Available`; return is allowed only from assigned
`In Use` hardware. Admin-only mutations are protected server-side.

Correction: Tightened database updates with conditional status predicates so
transitions are enforced at update time.

## 6. Critical Backend Tests

Prompt summary: Add focused pytest coverage for rental rules and admin-only user
creation.

Outcome: Tests cover invalid rental states, valid rental, invalid returns,
regular-user admin denial, and admin user creation.

Later correction: Added regression tests for unassigned returns, cross-user
return denial, admin return, and AI auditor fallback behavior.

## 7. AI Inventory Auditor

Prompt summary: Implement the backend AI Inventory Auditor feature.

Outcome: Added admin-only `POST /ai/audit`, deterministic inventory checks,
OpenAI SDK integration, strict structured JSON validation, redacted model input,
and deterministic fallback.

Correction: Kept deterministic findings authoritative and split the auditor into
route, checks, OpenAI adapter, report, and schema modules.

## 8. Vue Frontend

Prompt summary: Create the Vue 3 + TypeScript frontend scaffold, then implement
login, dashboard, admin panel, and AI auditor views.

Outcome: Added Vite setup, typed API client, JWT storage, session restore,
role-gated navigation, dashboard filters/sorting, rent/return actions, admin
forms, and the audit result UI.

Correction: Kept OpenAI calls backend-only and used frontend role checks only as
UX hints, with server-side authorization remaining authoritative.

## 9. Figma-Inspired UI Pass

Prompt summary: Compare the Vue frontend against Figma login/dashboard
wireframes and apply the most important UI improvements.

Outcome: Direct Figma MCP inspection was blocked by account permissions, so the
published Figma mock was reviewed in the browser. The implemented UI adopted a
standalone login screen, fixed sidebar, table-first hardware list, compact
status badges, and simplified admin table.

Simplifications kept: no Vue Router, no dedicated My Rentals screen, no modal
rewrite, and no fake AI assistant input.

## 10. Browser Testing and Deployed Bug Fix

Prompt summary: Use Chrome DevTools MCP to test the deployed Hardware Hub app,
admin flows first, then a newly created non-admin user.

Outcome: Smoke checks covered login, `/health`, dashboard sorting/filtering,
rent/return, admin visibility, AI Auditor, and deployed add-hardware behavior.

Correction: Fixed the numeric `Source ID` crash in `AdminView.vue` by converting
optional numeric input to a string before trimming.

## 11. Return Authorization Regression

Prompt summary: Fix a manually discovered return-permission bug.

Outcome: Backend return logic now allows regular users to return only devices
assigned to their own email, while admins can return any assigned `In Use`
device. The dashboard button mirrors the same rule.

Verification: Added regression tests for self-return, cross-user denial, and
admin return. Backend tests and frontend build passed.

## 12. Final Documentation

Prompt summary: Update final project documentation with honest implementation
status, AI usage, data strategy, prompts, decisions, deployment, tests, and
security notes.

Outcome: Updated README, AI log, prompt trail, and architecture decisions to
reflect the implemented MVP and remaining production gaps.
