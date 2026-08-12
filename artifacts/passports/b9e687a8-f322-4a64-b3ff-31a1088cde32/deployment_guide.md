# Production Deployment Guide

Release Tag: rel_b9e687a8
Commit Hash: 6a5bd98d12bcc2ba4da1e93e67eff6f8be5530da
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.