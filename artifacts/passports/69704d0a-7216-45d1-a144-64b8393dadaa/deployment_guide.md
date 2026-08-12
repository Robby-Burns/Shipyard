# Production Deployment Guide

Release Tag: rel_69704d0a
Commit Hash: efd3381257baa88eaf85db9183d07063347fed79
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.