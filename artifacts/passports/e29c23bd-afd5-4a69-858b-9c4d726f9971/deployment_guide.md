# Production Deployment Guide

Release Tag: rel_e29c23bd
Commit Hash: 7043286e37542bf537437cec0987d6b2e031ce7c
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.