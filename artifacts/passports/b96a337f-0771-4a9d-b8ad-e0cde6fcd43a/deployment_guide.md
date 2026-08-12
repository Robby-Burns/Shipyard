# Production Deployment Guide

Release Tag: rel_b96a337f
Commit Hash: 37d0b2e410705f84c13863eee1c8cfdb63343477
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.