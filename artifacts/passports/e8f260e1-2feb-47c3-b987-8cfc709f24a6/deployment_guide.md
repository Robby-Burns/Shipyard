# Production Deployment Guide

Release Tag: rel_e8f260e1
Commit Hash: c0d8537d017166bccfb18768cd07358665682a34
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.