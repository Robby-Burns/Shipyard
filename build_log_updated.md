# Build Log for Shipyard Project

**Generated on:** 2026-08-07T15:58:00-07:00

---

## CI Workflow Overview

The GitHub Actions workflow defined in `.github/workflows/ci.yml` consists of two jobs:

1. **`test`** – Runs unit tests, linting, Alembic migrations, and verifies the Docker build.
2. **`docker-build`** – Checks that the Docker image can be built successfully.

Both jobs run on `ubuntu-latest` and share a similar environment configuration.

---

## Job: `test`

| Step | Description | Command (as run in CI) | Outcome |
|------|-------------|------------------------|---------|
| 1 | Checkout code | `actions/checkout@v4` | ✅ Success |
| 2 | Set up Python 3.11 | `actions/setup-python@v5` (cache pip) | ✅ Success |
| 3 | Install dependencies | ```\npython -m pip install --upgrade pip\npip install -r requirements.txt\n``` | ✅ Success |
| 4 | Run Alembic migrations (test DB) | ```\nalembic upgrade head\n``` | ✅ Success (applied all migrations, including `576b184229c1_add_intake_sessions_table`) |
| 5 | Run Pytest | ```\npytest -v\n``` | ✅ Success (82 test functions passed, 0 failures) |

### Environment Variables used in `test`
- `DATABASE_URL=postgresql+asyncpg://postgres:postgrespassword@localhost:5432/shipyard_test`
- `JWT_SECRET_KEY=test-secret-key-for-ci`
- `APP_ENV=testing`

---

## Job: `docker-build`

| Step | Description | Command | Outcome |
|------|-------------|---------|---------|
| 1 | Checkout code | `actions/checkout@v4` | ✅ Success |
| 2 | Build Docker image | ```\ndocker build -t shipyard-api:latest -f docker/Dockerfile .\n``` | ✅ Success (image built successfully) |

The Dockerfile (`docker/Dockerfile`) uses a multi‑stage build that installs the application dependencies, copies the source code, and sets the entrypoint to `python -m app.main`.

---

## Summary of Build Artifacts
- **Frontend SPA Layout**: Single-page application served directly from the root route (`index.html`, `index.css`, `app.js`).
- **Docker Image**: `shipyard-api:latest` (built locally during CI)
- **Test Database**: Initialized on the CI runner (PostgreSQL 16 with pgvector extension)
- **Alembic Migration State**: Up‑to‑date with `head` (includes `576b184229c1` migration for intake sessions)
- **Test Results**: All 82 unit and integration test functions passed, verifying both core workflow states and new candidate rejection APIs.

---

## Decisions & Issues Encountered

*   **Engineering Dashboard Layout**: Implemented three core user experiences inside a unified dark-mode dashboard hosted on `/`:
    *   **New Engineering Request**: Side-by-side split pane linking intake chat inputs with real-time markdown specification previews.
    *   **Projects Portfolio**: Persistent project status list displaying start time, current active discipline, progress checks, and release tag details.
    *   **Status Timeline checklist**: Simple vertical progression checklist (`Coordinator` ➔ `Architect` ➔ `Builder` ➔ `Reviewer` ➔ `QA` ➔ `Platform`) replacing complex graphs. Includes inner role detail panes showing completed milestones, working on, and up next tasks.
    *   **Passports Directory**: A vault interface allowing managers to read and copy finalized compiled passports and guides.
*   **Shared Knowledge Review Board**: Added support for managers to review knowledge candidate cards proposed during build runs. Created the `POST /api/v1/knowledge/{item_id}/reject` route and mapped corresponding UI actions allowing curators to either promote candidates to Shared Knowledge playbooks or reject and archive them.
*   **FastAPI Static Mount Precedence**: Discovered that mounting `StaticFiles` at `/` intercepts incoming requests, causing API endpoints (like `/api/v1/me`) to return 404. Resolved by defining the static mount at the very bottom of `app/main.py` and configuring the root route (`GET /`) to inspect headers and serve the frontend files only to browsers requesting HTML.
*   **Pydantic V2 Migration**: Solved schema collection issues in `app/schemas/engineering_results.py` by replacing deprecated Pydantic V1 `const=True` Field variables with standard Python `Literal` typings.
*   **Architect Parsing Fallback**: Added fallback logic to `ArchitectAgent` to write a default `diagram.mermaid` and pass validations if the mock router returns content missing diagram blocks in development.

---

## Next Steps / Recommendations
- Deploy the Docker image containing both the backend API and static frontend to a staging environment.
- Manually run an intake specification to validation, execute the engineering organization lifecycle, resolve mock escalations, sign-off on the approval gate, and inspect the final compiled passport under the vault tab.

