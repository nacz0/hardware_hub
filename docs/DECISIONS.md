# Architecture Decisions

Concise decision log for the Hardware Hub MVP. Expand entries during
implementation when trade-offs become concrete.

| Decision | Rationale | Trade-off |
| --- | --- | --- |
| FastAPI + Vue 3 + SQLite | Fast to build, clear API/UI split, simple local setup. | SQLite is not the long-term production database. |
| Preserve dirty seed data | Data issues are part of the assignment and useful for auditing. | Import logic must flag issues instead of silently cleaning them. |
| Use assignment hardware fields | Keeps the model aligned with the brief: `name`, `brand`, `purchaseDate`, `status`, `notes`, `assignedTo`, `history`. | Future fields like category or condition are deferred. |
| Preserve statuses | Core statuses stay `Available`, `In Use`, `Repair`. | Other values become audit findings, not new states. |
| Local admin-created accounts | Matches internal-tool access control. | No self-registration or password reset in MVP. |
| JWT auth for MVP | Simple frontend/backend auth path. | No refresh tokens, revocation, or advanced session controls. |
| Inventory Auditor | Best fit for the dirty inventory dataset and admin workflow. | Semantic Search and Smart Assistant are deferred. |
| Deterministic checks before LLM | Critical data findings should be explainable and testable. | The first AI feature is partly rule-based by design. |
| Vercel + Railway targets | Practical deployment path for frontend and backend. | Railway + SQLite is demo-grade only. |
| GitHub Actions CI | Keeps tests/build checks visible. | Initial CI will be basic. |
| Single root `.gitignore` | This is a monorepo, so ignore rules live at the repository root instead of inside `backend/`. | Package-specific generated files need scoped paths when necessary. |
| Keep `main.py` tidy | FastAPI app setup should stay small; split routes, auth, and business logic into focused modules such as `hardware.py` when behavior grows. | More files, but clearer ownership for future updates. |
| Table-first frontend shell | The Figma mock emphasizes a simple internal tool: standalone login, fixed left navigation, and one table-focused work area at a time. | Kept state-based view switching instead of adding Vue Router for the MVP. |
| Keep Figma changes minimal | UI changes should improve spacing, navigation, badges, and dashboard structure without rewriting behavior. | Figma details like My Rentals, modals, icon polish, and AI search are deferred. |
