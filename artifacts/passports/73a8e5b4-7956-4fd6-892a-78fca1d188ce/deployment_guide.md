# Production Deployment Guide

Release Tag: rel_73a8e5b4
Commit Hash: 59ab357b7ffc3f25fc766760f41944027c04aff2
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.