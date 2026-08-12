# Production Deployment Guide

Release Tag: rel_9421e218
Commit Hash: 235fd392e872bf119cf1d96d3ae05dbb7e9246ea
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.