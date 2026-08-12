# Production Deployment Guide

Release Tag: rel_6e84d4e5
Commit Hash: a5326ea2110d96e9b895b3d13feb5967208e3f97
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.