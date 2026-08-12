# Shipyard Build Log

**Updated:** 2026-08-12
**Repository:** `Robby-Burns/Shipyard`
**Current commit:** `4df3de9 Harden multi-agent execution pipeline and implement tag robustness and retry/bypass layers`

---

## Current repository status

The latest committed work is pushed to `main`. Generated runtime artifacts under
`artifacts/` remain local and untracked; they are not part of the application
source or release commit.

Recent relevant commits:

| Commit | Change |
|---|---|
| `4df3de9` | Harden multi-agent execution pipeline, implement robust tag parser, structured outputs, transient retries, and native bypass |
| `fd64485` | Preserve the Architect's Mermaid/ADR source for Challenger verification |
| `051f3bc` | Harden OpenRouter routing, error handling, provider telemetry, and adaptive failover |
| `5c946d5` | Exclude batch-only OpenRouter models |
| `3286cc9` | Send only provider-supported OpenRouter parameters |
| `8a60f2d` | Add adaptive OpenRouter model routing and outcome storage |
| `b527373` | Replace retired OpenRouter model |
| `453306f` | Require a GitHub destination before engineering begins |
| `21bce65` | Continue truncated engineering specifications |
| `91c3867` | Use the Docker build for Railway deployment |
| `e45c4c9` | Pin the deployment runtime to Python 3.12 |
| `ae76d00` | Reduce engineering specification output size |

---

## Application capabilities built

### Engineering intake

- Chat-based engineering intake with persisted sessions and messages.
- File uploads for PDF, Markdown, JSON, YAML, and related text documents.
- Scanned-PDF OCR fallback using Poppler and Tesseract with size/page/DPI safeguards.
- Live engineering specification generation and continuation when output is truncated.
- Compact specification prompts and a configurable output budget:
  `INTAKE_SPEC_MAX_TOKENS` and `INTAKE_SPEC_MAX_CONTINUATIONS`.
- Specifications remain available for conversation and revision before approval.
- A GitHub repository destination is required before the engineering pipeline starts.

### Multi-agent engineering pipeline

- Coordinator creates the build plan.
- Architect produces Mermaid diagrams and ADRs.
- Builder produces implementation files and test results, then uses the repository adapter to commit generated code.
- Reviewer evaluates the implementation.
- QA validates test and quality results.
- Platform reports metrics and proposes knowledge candidates.
- Challenger verifies each stage and supplies correction feedback for bounded retries.
- Human approval gates production deployment and passport compilation.
- Pause, kill, restart, escalation, and escalation-resolution controls are available.

### Repository and deployment support

- Repository adapter interfaces with GitHub support and mock development adapters.
- Railway deployment configuration uses the root `Dockerfile`, `railpack.json`, and `Procfile`.
- Docker runtime uses Python 3.12, PostgreSQL-compatible database support, Poppler, and Tesseract.
- Alembic migrations run during container startup.
- PgBouncer-safe PostgreSQL connection settings disable asyncpg prepared-statement caching where required.

### OpenRouter integration

- Model catalog discovery is cached in the database and refreshed independently from request execution.
- Catalog filtering removes non-text, batch-only, and request-incompatible models.
- Model-level fallback uses OpenRouter's `models[]` request field, capped at three candidates.
- Provider-level failover uses `allow_fallbacks` and `require_parameters`.
- OpenRouter's normal uptime-aware load balancing remains the default; provider sorting can optionally be configured as `price`, `throughput`, or `latency`.
- Retired model IDs are normalized through a compatibility alias.
- Provider-specific token parameters support both `max_tokens` and `max_completion_tokens`.
- HTTP errors preserve typed OpenRouter/provider details, including payment, rate-limit, authentication, validation, and provider failures.
- HTTP 200 responses with `finish_reason: "error"`, missing choices, missing text, or invalid payloads are treated as failures instead of successful completions.
- `Retry-After` is preserved for rate-limit and retryable availability errors.
- `X-OpenRouter-Metadata: enabled` records selected provider, fallback attempts, and routing metadata when returned.
- Actual response cost is used when OpenRouter reports it; otherwise cost is estimated from catalog pricing.
- Routing outcomes record model, provider details, latency, cost, success, error type, and privacy-safe task features.
- Verified Challenger results feed back into model quality scores. Routing uses those results with reliability, latency, cost, catalog evidence, and limited exploration; it does not guess quality from model names.

---

## Architect verification fix

The latest fix addresses a false escalation in architecture design:

1. The Architect correctly generated `<diagram>```mermaid ... ```</diagram>` and `<adr id="..."> ... </adr>` tags.
2. Shipyard then replaced the tagged source with JSON before sending it to the Challenger.
3. The Challenger received JSON and reported that the required tags were missing.

The Architect now preserves the original tagged document in `output_text`, stores
the parsed files and structured architecture summary separately in `artifacts`,
and explicitly instructs the model not to return JSON for the verified source.

---

## Verification status

The complete Pytest suite (comprising 134 automated unit and integration tests) has been run locally in the Python 3.12 environment and passes successfully.

The CI workflow configuration (`.github/workflows/ci.yml`) has been updated and aligned:
- Bumped the Python version to `3.12` to match `.python-version`, `Dockerfile`, and the Railway deployment runtime.
- Updated the CI Docker build step to use the root `Dockerfile` instead of `docker/Dockerfile` to match production.

---

## Deployment checklist

- Confirm Railway is deploying commit `fd64485` or a later commit.
- Verify the CI build passes successfully using Python 3.12 and the root Dockerfile.
- Run Alembic migrations and the complete Pytest suite in CI.
- Exercise an intake upload, specification continuation, architecture verification,
  Builder repository commit, and approval flow in staging.
- Confirm the OpenRouter API key has sufficient credits for the configured output
  budget.
