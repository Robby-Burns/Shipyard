# Production Deployment Guide

Release Tag: rel_3cbf33f8
Commit Hash: 2b68f0a4c8ae6e901871212c066558ade7f1e21e
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.