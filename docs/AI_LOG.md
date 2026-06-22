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

Placeholder:

- AI suggestion:
- Issue found:
- Manual correction:
- Verification:
