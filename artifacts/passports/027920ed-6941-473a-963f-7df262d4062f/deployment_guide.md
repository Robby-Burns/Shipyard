# Production Deployment Guide

Release Tag: rel_027920ed
Commit Hash: c309dea87bd5e28870bc3ee3f2f6683478fd85ee
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.