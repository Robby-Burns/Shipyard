# Production Deployment Guide

Release Tag: rel_0944465c
Commit Hash: 1db83fff9578c379762156a7bcd1c03308293382
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.