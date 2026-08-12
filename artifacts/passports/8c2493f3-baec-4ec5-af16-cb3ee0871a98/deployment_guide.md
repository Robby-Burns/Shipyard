# Production Deployment Guide

Release Tag: rel_8c2493f3
Commit Hash: mock-hash
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.