# Production Deployment Guide

Release Tag: rel_df45f98d
Commit Hash: 91c3acf7711ab7ff28b071f36714c9876b377c01
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.