# Production Deployment Guide

Release Tag: rel_25ec54fe
Commit Hash: 1d20d44d137de0cf66c41abd7cd88f8e454cb702
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.