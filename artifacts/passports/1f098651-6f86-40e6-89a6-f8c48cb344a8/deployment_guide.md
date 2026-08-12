# Production Deployment Guide

Release Tag: rel_1f098651
Commit Hash: f2122ce891ecfe81943e51505db176d61745767f
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.