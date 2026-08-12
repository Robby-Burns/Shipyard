# Production Deployment Guide

Release Tag: rel_78ae13dc
Commit Hash: 93dfb7dd2ef637e1574f86fd3d43a20cff5f55f3
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.