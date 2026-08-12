# Production Deployment Guide

Release Tag: rel_a3688f3b
Commit Hash: a3ead72fdb4944fb46e26dbf57e0269be50a02d8
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.