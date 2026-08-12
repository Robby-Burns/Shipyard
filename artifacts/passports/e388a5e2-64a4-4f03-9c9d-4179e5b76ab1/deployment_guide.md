# Production Deployment Guide

Release Tag: rel_e388a5e2
Commit Hash: 7c033765b70576863ced71ef4cb0f18862c26ff6
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.