# Production Deployment Guide

Release Tag: rel_79233151
Commit Hash: 296cb6a0ed34643d307b9f4f4766c0ce2ed6543a
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.