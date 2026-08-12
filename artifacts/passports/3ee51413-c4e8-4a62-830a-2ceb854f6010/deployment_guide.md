# Production Deployment Guide

Release Tag: rel_3ee51413
Commit Hash: 9e9e74cc69e78579e7f0b1d81835e6143acde5a3
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.