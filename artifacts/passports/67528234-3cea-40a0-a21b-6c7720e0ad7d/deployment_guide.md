# Production Deployment Guide

Release Tag: rel_67528234
Commit Hash: 11632d310e503de08e81dd0ed51b80c92620c8c9
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.