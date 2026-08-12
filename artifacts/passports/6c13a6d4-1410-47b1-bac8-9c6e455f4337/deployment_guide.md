# Production Deployment Guide

Release Tag: rel_6c13a6d4
Commit Hash: 7d61400fda16290a4a97610577336792f5f379c7
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.