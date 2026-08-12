# Production Deployment Guide

Release Tag: rel_7ac9256e
Commit Hash: 96068ff4f7d116f38d249a371cbd7b6ebd01e785
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.