# Production Deployment Guide

Release Tag: rel_815b851c
Commit Hash: d24f847ec5ddc086f0ca1ebd8967c45f7e7deefe
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.