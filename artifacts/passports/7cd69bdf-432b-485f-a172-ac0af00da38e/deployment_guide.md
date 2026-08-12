# Production Deployment Guide

Release Tag: rel_7cd69bdf
Commit Hash: ebc4dec843cd5f63e44b82f9fb7797a36c0d6bcb
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.