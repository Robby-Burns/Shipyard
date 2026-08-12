# Production Deployment Guide

Release Tag: rel_4f052b32
Commit Hash: 66fb69f42364d39ce7c3d361d0b045ebe18dddc5
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.