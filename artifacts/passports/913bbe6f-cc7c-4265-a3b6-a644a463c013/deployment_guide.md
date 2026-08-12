# Production Deployment Guide

Release Tag: rel_913bbe6f
Commit Hash: 281e12f7ac57ce3d2a3670825cc1ca6b4767bd65
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.