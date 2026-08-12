# Production Deployment Guide

Release Tag: rel_ab8366ec
Commit Hash: 35985e7438211c0e4e05453a8094d3ecbb31d2d5
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.