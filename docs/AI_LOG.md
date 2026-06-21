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
