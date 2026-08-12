# Production Deployment Guide

Release Tag: rel_f86c27a0
Commit Hash: 63f14291a3d395d2dd0017f60bd532c96ce3a2c9
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.