# AI Development Log

This project used AI assistance as an engineering accelerator. AI output was not
treated as production proof; code, tests, browser behavior, and assignment scope
were manually reviewed.

## Tools Used

- Codex: planning, implementation, refactoring, tests, documentation, and review.
- Figma MCP: attempted source-file inspection, but it was not used for design
  extraction because the connected account was not authorized for that file.
- Chrome DevTools MCP: copied the published Figma-site design direction,
  browser smoke testing, deployed app validation, console and network checks.
- OpenAI API: runtime Inventory Auditor integration through the backend.

## How AI Was Used

Codex helped break the work into a small FastAPI/Vue MVP, draft the backend API
shape, implement route modules, write critical pytest coverage, build frontend
views, and keep the docs aligned with the implementation.

Important AI-generated decisions were reviewed against the assignment. One early
AI draft over-expanded the inventory model with generic asset-management fields.
That was corrected back to the assignment fields: `name`, `brand`,
`purchaseDate`, `status`, `notes`, `assignedTo`, and `history`.

## Figma MCP Authorization Gap

Figma MCP was not used to copy or inspect the actual source design because the
connected account did not have authorization for the Figma file. That means no
nodes, component structure, variables, or design-system metadata were imported
from Figma MCP.

The useful outcome was discovering that limitation early and avoiding a false
claim that the app was generated from or directly synchronized with the Figma
file.

## How Chrome DevTools MCP Helped

Chrome DevTools MCP was used for practical browser validation:

- Opening the published Figma site and copying the visible design direction:
  standalone login, fixed sidebar, table-first hardware view, compact status
  badges, and a simple admin table.
- Login as admin and regular user.
- Dashboard loading, filtering, sorting, rent, and return flows.
- Admin panel access control and hardware creation.
- AI Auditor request and fallback display.
- Deployed app smoke checks after Vercel/Railway configuration.
- Console and network errors during UI actions.

It found a concrete deployed bug: Admin Panel -> Add hardware failed with
`U.trim is not a function` when numeric `Source ID` was filled. The fix was to
normalize optional numeric input before trimming in the Vue admin form.

So the design workflow was: Figma MCP attempted but blocked by authorization;
Chrome DevTools MCP used to view the published Figma-site mock; then the Vue UI
was manually adjusted to match the visible layout patterns.

## How the OpenAI API Was Used

The backend Inventory Auditor runs deterministic checks first. If
`OPENAI_API_KEY` is configured and `OPENAI_AUDIT_MOCK` is not enabled, it calls
OpenAI through the official Python SDK and requests a strict structured JSON
report.

The model receives a minimized inventory view and deterministic findings. Raw
`assigned_to`, `notes`, and `history` values are not sent; the backend sends
booleans such as whether an assignee exists and whether damage-related text was
detected.

The OpenAI response is advisory only. The backend validates it against a Pydantic
schema, merges deterministic findings back in, and falls back to deterministic
output if the API key is missing, mock mode is enabled, the request fails, or the
model returns invalid structure.

## Concrete AI Correction Example

Issue found during AI-assisted browser testing:

- The deployed admin add-hardware flow crashed when `Source ID` was entered as a
  number.
- The browser showed a `trim` error because form normalization assumed text.
- The fix updated `optionalNumber` to convert the value with `String(value ?? '')`
  before trimming.
- Verification: frontend production build passed, and a deployed Chrome MCP
  retest created a temporary hardware row with numeric source ID successfully.

Separate manual testing later found a more important authorization gap: any
authenticated user could return any assigned `In Use` device. That bug was not
caught by the earlier AI-assisted tests. The backend now limits regular users to
returning devices assigned to their own email, while admins can return any
assigned device. Regression tests were added.

## What Was Manually Reviewed

- Assignment scope and allowed hardware fields/statuses.
- Backend auth, role guards, rent/return transitions, and AI audit route.
- Frontend role gating and visible user flows.
- Dirty seed data handling.
- Test coverage for critical rental, return, admin, and AI audit behavior.
- Production build output for the frontend.
- Browser behavior for login, dashboard, admin, and auditor views.
- Documentation claims, especially around production readiness.

## Data Strategy

The initial dataset was treated as source data, not clean application truth. The
app imports it into SQLite while preserving dirty values:

- Duplicate source IDs remain as `external_id` duplicates.
- Missing brands remain missing.
- Invalid date formats and null dates remain visible.
- Future purchase dates remain visible.
- Unknown statuses remain visible.
- Notes/history that imply damage remain stored for audit context.
- `In Use` rows without assignees remain visible but are guarded from invalid
  return actions.

AI helped identify two integration challenges:

- The first AI draft tried to normalize the domain into a broader inventory
  model. Manual review corrected this so the app stayed aligned with the
  assignment fields.
- The auditor design needed to preserve dirty data while still protecting core
  workflows. The final approach keeps dirty records visible, uses deterministic
  checks to flag them, and prevents unsafe state transitions.

The dataset is not automatically repaired by AI. Future production work should
add an explicit admin correction workflow with audit history.
