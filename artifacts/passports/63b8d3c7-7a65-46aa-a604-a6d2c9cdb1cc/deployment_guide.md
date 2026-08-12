# Production Deployment Guide

Release Tag: rel_63b8d3c7
Commit Hash: 33539753c35a79bd13b30e01937eda0228599c14
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.