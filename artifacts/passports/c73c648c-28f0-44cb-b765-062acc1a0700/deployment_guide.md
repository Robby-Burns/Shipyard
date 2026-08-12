# Production Deployment Guide

Release Tag: rel_c73c648c
Commit Hash: 12cd809294f1be5819b6b100e9ea22054e9507d0
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.