# AI Development Log

Short log of planned and actual AI usage. Add concrete examples as the project
is implemented.

## Tools

- Codex: planning, docs, implementation help, tests, review.
- Figma MCP: UI guidance for dashboard/admin flows.
- Chrome DevTools MCP: browser validation after frontend exists.
- OpenAI API: runtime Inventory Auditor.

## Workflow

AI may assist with implementation, but output is reviewed before acceptance.
Tests, assignment requirements, and manual browser checks remain the source of
truth.

## Inventory Auditor

The backend should run deterministic checks first, then send a compact inventory
summary to the OpenAI API for an admin-readable audit.

The auditor can flag duplicate IDs, invalid dates, missing brands, invalid
statuses, unsafe available items, and `In Use` items without `assignedTo`.

The auditor is advisory. It must not update records automatically.

## Figma MCP Plan

Use for layout guidance only:

- Dashboard columns: Name, Brand, Purchase Date, Status
- Admin hardware/user management screens
- Simple internal-tool usability checks

### Figma/Chrome UI Review

Direct Figma MCP inspection of the Make file was blocked because the connected
account did not have edit access. Workaround: inspect the published Figma site
with the Chrome-backed browser MCP at `https://serene-mural-33249528.figma.site/`.

Observed wireframe details:

- Standalone centered login card with email/password fields and a dark login
  button.
- Authenticated app shell with a fixed left sidebar, `Hardware Manager` brand,
  navigation items, and bottom logout.
- Table-first hardware list with compact rows, status badges, and rent actions.
- Admin table with serial numbers, status badges, and compact action controls.

Applied only layout guidance from this review. Existing Vue API calls and
backend behavior remained the source of truth.

## Chrome DevTools MCP Plan

Use after the frontend runs:

- Login flow
- Dashboard filtering/sorting
- Rent/return requests
- Admin-only access
- Console and network errors

## AI Correction Example

- AI-assisted review: Chrome DevTools MCP smoke-tested login, dashboard
  rendering, filtering/sorting, rent/return actions, admin visibility, and the
  AI auditor request against the running app.
- Issue found: dirty seed rows were valid auditor input, but two core workflows
  needed tighter handling: invalid/missing purchase dates sorted ahead of valid
  dates in descending order, and an `In Use` row without `assignedTo` exposed a
  usable return action.
- Manual correction: kept dirty records intact, made dashboard date sorting
  accept only strict `YYYY-MM-DD` dates and place invalid/missing dates after
  valid dates, disabled unassigned returns in the UI, and rejected unassigned
  returns in the backend.
- Verification: `python -m pytest backend\tests` passed with 14 tests, and
  `npm run build` passed from `frontend/`.

## Deployed Chrome MCP Regression

- Chrome DevTools MCP found deployed Admin Panel -> Add hardware failed with
  `U.trim is not a function` when `Source ID` was filled.
- Fixed `AdminView.vue` by normalizing optional numeric input before trimming;
  `npm run build` passed from `frontend/`.
- Deployed retest created a temporary row with numeric source ID and no trim
  error. Cleanup briefly blocked on the browser confirm dialog during Chrome MCP
  use; after confirmation, a fresh inventory check showed the row was gone.

## Manual Testing Gap

- Manual testing later found a return-authorization bug: any authenticated user
  could return any assigned `In Use` device.
- This was not caught by the earlier extensive AI-assisted testing and Chrome
  MCP smoke checks. Those checks covered login, filtering/sorting, happy-path
  rent/return behavior, admin visibility, AI Auditor, unassigned dirty rows,
  and deployed admin workflows, but missed the cross-user ownership case.
- Correction: backend return authorization now limits regular users to devices
  assigned to their own email, while admins can return any assigned `In Use`
  device. The dashboard Return button mirrors the same client-side rule.
- Verification: added regression tests for self-return, cross-user denial, and
  admin return. `python -m pytest backend\tests` passed with 17 tests, and
  `npm run build` passed from `frontend/`.
