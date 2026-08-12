# Production Deployment Guide

Release Tag: rel_99c4e9d5
Commit Hash: 21c95e0f785184e98210f17ae5cd925aff5f8dfa
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.