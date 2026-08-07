# Shipyard Builder Guidelines

These guidelines define the coding standards, style rules, and repository conventions that the **Builder Agent** must follow when writing code.

---

## 1. Programming Languages & Frameworks
*   **Backend:** FastAPI with Python 3.11+.
*   **Database ORM:** SQLAlchemy 2.0 (async queries only, using `select` and `execute` via `AsyncSession`).
*   **Database Migrations:** Alembic for all schema updates.
*   **Testing:** `pytest` with async support (`pytest-anyio` or `pytest-asyncio`).

---

## 2. Code Quality & Formatting
*   **PEP 8 Compliance:** All code must adhere to PEP 8 standards.
*   **Type Hinting:** Mandatory for all function signatures, parameters, and return values.
*   **Linting & Formatting:** Code should be formatted to be compatible with automated tools (e.g., Black/Ruff).
*   **Naming Conventions:**
    *   Classes: `PascalCase`
    *   Functions, Methods, Variables: `snake_case`
    *   Constants: `UPPER_SNAKE_CASE`

---

## 3. Database & SQL Conventions
*   **No Synchronous Calls:** Never use synchronous SQLAlchemy methods (like `.commit()`, `.refresh()`, or `.scalar()`) without their `await` prefix.
*   **No Model Attribute Lazy-Loading:** Always use joined/selectin loading for relationships in async contexts to avoid `MissingGreenlet` errors.
*   **Aggregation:** Use SQL function aggregation (e.g., `func.count()`) instead of pulling entire result sets in-memory for counts or sums.

---

## 4. Documentation & Docstrings
*   **Module-level Docstrings:** Describe the module's overall responsibility at the top of every file.
*   **Function/Method Docstrings:** Include a brief description, parameter details, and return values using the Google or Sphinx format.
*   **Inline Comments:** Explain the *why*, not the *what*, of complex logic.

---

## 5. Testing Requirements
*   **Unit Tests:** Every new module or service must be accompanied by unit tests covering:
    *   Happy path scenarios.
    *   Edge cases and input validation failures.
    *   Error boundaries and expected exception raises.
*   **Test Isolation:** Use mock data/databases (e.g., SQLite in-memory or transactions) to ensure test isolation. Do not pollute the main database.
*   **No Prints in Tests:** Use assertions or standard logging inside tests.

---

## 6. Git & Version Control
*   **Branching:** Code should be prepared in feature branches.
*   **Commit Messages:** Follow the conventional commit format (e.g., `feat: add rate limiting middleware` or `fix: resolve jwt expiration logic`).
*   **Atomic Commits:** Keep commits small and focused on a single change.
