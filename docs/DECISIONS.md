# Architecture Decisions

Concise decision log for the Hardware Hub MVP. These decisions describe the
implemented project, including trade-offs that would need refactoring before
production use.

| Decision | Rationale | Trade-off |
| --- | --- | --- |
| Use assignment hardware fields as the source of truth | Keeps the app aligned with the brief: `name`, `brand`, `purchaseDate`, `status`, `notes`, `assignedTo`, `history`. | Broader asset fields like category, condition, department, and serial number are deferred. |
| Preserve `Available`, `In Use`, and `Repair` statuses | Matches the required workflow and avoids inventing extra state. | Dirty values such as `Unknown` are treated as audit findings, not normalized states. |
| Preserve dirty seed data | Data-quality problems are part of the assignment and useful for the AI audit feature. | The UI must tolerate invalid dates, missing brands, duplicate IDs, and incomplete assignments. |
| Store source IDs as `external_id` | Allows duplicate source IDs to remain visible while SQLite still has a reliable primary key. | Admins see both internal row identity and source data issues. |
| FastAPI + Vue 3 + SQLite | Fast to build, easy to run locally, clear API/UI split. | SQLite and direct SQL functions are not the long-term production persistence design. |
| Keep backend modules split by responsibility | `main.py` stays focused on app setup while auth, hardware, users, database, and AI audit logic live in separate modules. | More files, but clearer ownership and easier testing. |
| Use bcrypt for password hashing | Avoids storing plaintext passwords and is enough for an MVP credential store. | Missing production features such as password reset, account lockout, and password policy management. |
| Use JWT access tokens for MVP auth | Simple to integrate between FastAPI and Vue. | No refresh tokens, revocation, device tracking, or session management. |
| Enforce role checks server-side | Frontend role gating is only UX; the API must remain authoritative. | Every protected route needs explicit backend dependencies/tests. |
| Admin-created accounts only | Fits an internal hardware tool and avoids self-registration scope. | No invite workflow, deactivation, user list, or password reset yet. |
| Return authorization checks ownership | Regular users should only return hardware assigned to themselves; admins may return any assigned item. | More conditional logic, but it closes a real cross-user permission bug. |
| Conditional database updates for state transitions | Rent/return operations should verify expected status at mutation time, not only before mutation. | Direct SQL is slightly more verbose but safer under concurrent requests. |
| Deterministic audit checks before OpenAI | Critical data findings must be explainable, repeatable, and testable. | The AI feature is intentionally partly rule-based. |
| Redact sensitive audit fields before OpenAI | Raw assignee, notes, and history may contain personal or sensitive information. | The model gets less context, so some recommendations must rely on derived flags. |
| Treat AI output as advisory only | LLM output should not directly mutate inventory or override deterministic findings. | Admins still need to perform corrections manually. |
| Use OpenAI structured output with fallback | A schema keeps the UI predictable, and deterministic fallback keeps the feature usable without an API key. | The app does not persist audit runs or compare report history. |
| Table-first frontend shell | The Figma mock and internal-tool use case favor dense, scannable tables over a marketing-style UI. | More advanced screens such as My Rentals and polished modals are deferred. |
| State-based view switching instead of Vue Router | Three screens did not justify router setup during the MVP window. | Deep links, route guards, and browser history are missing. |
| Keep admin user display session-local | The backend only implements user creation, not listing. | Admins cannot review all persisted users through the UI yet. |
| GitHub Actions runs backend tests and frontend build | Keeps the most important checks visible on push and pull request. | No browser E2E tests or deployment smoke tests in CI yet. |
| Vercel frontend and Railway backend config | Practical deployment path with minimal repo configuration. | Railway + SQLite is demo-grade unless persistent storage or Postgres is added. |
| Do not claim production readiness | The MVP lacks hardening, observability, durable storage, and complete admin workflows. | Documentation must be explicit about gaps instead of overselling the result. |
