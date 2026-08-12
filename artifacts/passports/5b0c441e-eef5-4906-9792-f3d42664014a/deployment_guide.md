# Production Deployment Guide

Release Tag: rel_5b0c441e
Commit Hash: 41981daa54e7c53c7ef00ee757ce412a394df62c
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.