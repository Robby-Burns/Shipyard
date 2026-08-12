# Production Deployment Guide

Release Tag: rel_af72346e
Commit Hash: 0aea11f0489b5a4a31cba83425478c841e72ea23
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.