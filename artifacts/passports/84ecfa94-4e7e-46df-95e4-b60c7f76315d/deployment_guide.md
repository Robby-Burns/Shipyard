# Production Deployment Guide

Release Tag: rel_84ecfa94
Commit Hash: 9540068ce57e2c18577f0ad68636a4e3183b0fc7
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.