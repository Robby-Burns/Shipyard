# Production Deployment Guide

Release Tag: rel_5df2d4af
Commit Hash: 434190866eb6a579c6a4c91c9001d717f8592345
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.