# Production Deployment Guide

Release Tag: rel_d5e1f311
Commit Hash: 53998b9f0e2d3d7fad9954670ce314a988672d17
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.