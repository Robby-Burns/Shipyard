# Production Deployment Guide

Release Tag: rel_090b5f85
Commit Hash: 62b217b348043b7a2c29bfc7f3af0bb127e586fc
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.