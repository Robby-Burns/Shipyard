# Production Deployment Guide

Release Tag: rel_44e89ed9
Commit Hash: 39853cedd43f3914d9d70722a04eabb8006291ea
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.