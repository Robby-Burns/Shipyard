# Production Deployment Guide

Release Tag: rel_e8c7e73c
Commit Hash: c5d341d7898cf7d57de0c2c68e2289d1ece6b0cf
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.