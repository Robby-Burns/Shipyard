# Production Deployment Guide

Release Tag: rel_7797c0d2
Commit Hash: 95263c7bca5bcfec059d91f4095806330a057a3d
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.