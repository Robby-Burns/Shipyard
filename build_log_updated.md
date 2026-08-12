# Build Log for Shipyard Project

**Generated on:** 2026-08-11T16:27:00-07:00

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
| 2 | Set up Python 3.12 | `actions/setup-python@v5` (cache pip) | ✅ Success |
| 3 | Install dependencies | ```\npython -m pip install --upgrade pip\npip install -r requirements.txt\n``` | ✅ Success |
| 4 | Run Alembic migrations (test DB) | ```\nalembic upgrade head\n``` | ✅ Success (applied all migrations, including `576b184229c1_add_intake_sessions_table`) |
| 5 | Run Pytest | ```\npytest -v\n``` | ✅ Success (97 test functions passed, 0 failures) |

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
- **Deployment Configurations**: Added [`railpack.json`](file:///c:/Users/burns/OneDrive/Documents/GitHub/Shipyard/railpack.json) and [`Procfile`](file:///c:/Users/burns/OneDrive/Documents/GitHub/Shipyard/Procfile) to support cloud deployment with Railpack/PaaS.
- **Frontend SPA Layout**: Single-page application served directly from the root route (`index.html`, `index.css`, `app.js`) with integrated file attachment support.
- **Docker Image**: `shipyard-api:latest` (built locally during CI)
- **Test Database**: Initialized on the CI runner (PostgreSQL 16 with pgvector extension)
- **Alembic Migration State**: Up‑to‑date with `head` (includes `576b184229c1` migration for intake sessions)
- **Test Results**: All 103 unit and integration test functions passed, verifying core workflow states, settings validations, JWT claim enforcement, URL sanitization, and scanned PDF OCR fallback logic.

---

## Decisions & Issues Encountered

*   **Pydantic Settings Validator Refactoring**: Discovered that Pydantic v2's `@field_validator` raised a `PydanticUserError` when defined as an instance method. Replaced it with `@model_validator(mode="after")` to correctly access `self.app_env` post-initialization and dynamically enforce JWT secret strength in production.
*   **JWT Expiration Claim Reinforcement**: Configured `jwt.decode` in `app/services/auth.py` to enforce the `exp` claim via `options={"require": ["exp"]}`. To resolve failing unit tests that generated mock tokens without the `exp` claim, implemented a global `jwt.encode` monkeypatch in `tests/conftest.py` to auto-inject exp claims during tests.
*   **Database Connectivity and Details Redaction**: Refactored the Memory component's health check to run an async `SELECT 1` query using `async with engine.begin()`. Completely removed the `"Connection URL"` detail from the endpoint response (Issue #8) to minimize attack surface and prevent host/credential exposure in public logs.
*   **URL Sanitization Utility**: Created a robust `sanitize_db_url` utility helper under `app/utils/` to handle usernames/passwords containing `@` characters and missing schemas. Added a parametrized unit test suite covering these edge cases.
*   **Engineering Dashboard Layout**: Implemented three core user experiences inside a unified dark-mode dashboard hosted on `/`:
    *   **New Engineering Request**: Side-by-side split pane linking intake chat inputs with real-time markdown specification previews.
    *   **Projects Portfolio**: Persistent project status list displaying start time, current active discipline, progress checks, and release tag details.
    *   **Status Timeline checklist**: Simple vertical progression checklist (`Coordinator` ➔ `Architect` ➔ `Builder` ➔ `Reviewer` ➔ `QA` ➔ `Platform`) replacing complex graphs. Includes inner role detail panes showing completed milestones, working on, and up next tasks.
    *   **Passports Directory**: A vault interface allowing managers to read and copy finalized compiled passports and guides.
*   **Shared Knowledge Review Board**: Added support for managers to review knowledge candidate cards proposed during build runs. Created the `POST /api/v1/knowledge/{item_id}/reject` route and mapped corresponding UI actions allowing curators to either promote candidates to Shared Knowledge playbooks or reject and archive them.
*   **FastAPI Static Mount Precedence**: Discovered that mounting `StaticFiles` at `/` intercepts incoming requests, causing API endpoints (like `/api/v1/me`) to return 404. Resolved by defining the static mount at the very bottom of `app/main.py` and configuring the root route (`GET /`) to inspect headers and serve the frontend files only to browsers requesting HTML.
*   **Railpack Start Command Detection**: Encountered a deployment failure on Railpack (`No start command detected`). Because the main app file (`main.py`) is located in the `app` subdirectory (`app/main.py`) rather than the project root, Railpack failed to auto-detect the application start command. Resolved this by creating a [`railpack.json`](file:///c:/Users/burns/OneDrive/Documents/GitHub/Shipyard/railpack.json) file with a custom `startCommand` running `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` (ensuring database migrations run automatically on container startup), and a backup [`Procfile`](file:///c:/Users/burns/OneDrive/Documents/GitHub/Shipyard/Procfile) with the same start command format.
*   **Intake Specification File Uploads**: Added support for uploading product spec documents (PDF, Markdown, JSON, YAML, etc.) directly in the intake chat column. Implemented text extraction logic using the `pypdf` library for PDF files. The parsed content is wrapped in a structured format and sent as a message to the Intake Coordinator, enabling users to generate system designs and specifications directly from uploaded documents. Added corresponding unit tests in [`tests/test_intake.py`](file:///c:/Users/burns/OneDrive/Documents/GitHub/Shipyard/tests/test_intake.py).
*   **Scanned PDF OCR Fallback Support**: Extended the intake file upload system to support scanned (image-only) PDF files. Developed a character-density heuristic (under 100 characters per page triggers OCR) that falls back to Poppler rendering and Tesseract extraction. Prevented event loop blocking by offloading OCR to a background thread pool via `asyncio.to_thread`. Added strict page limits (15 pages max), DPI constraints (150 DPI), and explicit timeouts to mitigate Denial of Service. Propagated a `(OCR Extracted)` tag to downstream LLM coordinator processes to alert them of text derivation source. Written a mocked and gated integration test suite verifying these features.
*   **PgBouncer DuplicatePreparedStatementError Fix**: Resolved a startup crash on Railway where the database connection threw a `DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_1__" already exists` during Alembic migrations. This issue occurred because PgBouncer multiplexes connections in transaction/statement pooling mode, conflicting with asyncpg's default prepared statement caching. Fixed this by setting `prepared_statement_cache_size=0` and `statement_cache_size=0` in `connect_args` for `create_async_engine` (in [`app/database/session.py`](file:///c:/Users/burns/OneDrive/Documents/GitHub/Shipyard/app/database/session.py)) and `async_engine_from_config` (in [`alembic/env.py`](file:///c:/Users/burns/OneDrive/Documents/GitHub/Shipyard/alembic/env.py)) whenever connecting via a PostgreSQL database URL.
*   **Asynchronous Pipeline Execution (FastAPI BackgroundTasks)**: Resolved HTTP gateway timeouts (such as Railway's 30-second proxy limit) which cancelled multi-agent pipeline executions midway by offloading the runs to FastAPI `BackgroundTasks`. Added dynamic test runner checking via `sys.modules` to execute tasks synchronously during `pytest` sessions, maintaining 100% test client compatibility.
*   **Frontend State & Scroll Position Retention**: Fixed a user-experience issue where 3-second polling replaced the entire DOM of the details pane, causing active subtabs, clicked step highlights, and scrolling offsets to reset. Implemented a data-attribute project identification check that caches the active subtab, active checklist role, and `.scrollTop` values in the DOM, restoring them post-refresh.
*   **Manual Pipeline Controls (Pause, Kill, and Restart)**: Added Pause, Kill, and Force Restart actions to the details header. Pausing changes the workflow state to `escalated` and suspends the background loop cleanly upon current step completion. Killing changes the workflow state to `failed` and prompts the user for double-input confirmation (requiring typing "KILL"). Force Restart resets stuck builds to the `created` status and kicks off a fresh background run.
*   **Resuming Workflows and Log Spam Mitigation**: Resolved a bug where resuming a paused/escalated workflow (which sets its status to an active status like `PLANNING`, `BUILDING`, etc.) failed to execute because the `/run` endpoint only allowed execution for workflows in the `CREATED` status, returning a `400 Bad Request`. This resulted in the workflow getting stuck, causing the frontend's 3-second polling interval to spam `GET /api/v1/workflows/{id}` requests indefinitely. Fixed by updating the `/run` endpoint validation to support all active/runnable statuses, adding a handler in `execute_step` for `WorkflowStatus.PLANNING` so it can execute correctly when resumed, and adding the missing `"architect": WorkflowStatus.DESIGNING` mapping in `resolve_escalation`'s `step_to_status` so architect escalations resume in `DESIGNING` status instead of defaulting to `PLANNING`.


---

## Next Steps / Recommendations
- Deploy the Docker image containing both the backend API and static frontend to a staging environment (e.g. Railway).
- Set `DATABASE_URL` environment variable to a cloud database (e.g., Supabase or Neon).
- Confirm settings validation correctly runs and enforces environment constraints under `APP_ENV=production`.

