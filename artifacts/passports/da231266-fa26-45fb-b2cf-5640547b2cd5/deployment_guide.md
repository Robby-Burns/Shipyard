# Production Deployment Guide

Release Tag: rel_da231266
Commit Hash: d892266487188cba770dce1490672c26f90c9fbb
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.