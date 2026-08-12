# Production Deployment Guide

Release Tag: rel_18bb5771
Commit Hash: 283755935477ed6e3a9a173b38c3f2ed3b7b469c
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.