# Production Deployment Guide

Release Tag: rel_b227cc3f
Commit Hash: 94cf4b168b572919a6a8cc69aa27e09b12f49f61
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.