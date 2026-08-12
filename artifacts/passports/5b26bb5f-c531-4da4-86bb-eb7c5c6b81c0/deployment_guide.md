# Production Deployment Guide

Release Tag: rel_5b26bb5f
Commit Hash: 8c11550a00cf98f0329109b65e35882d5a0becd2
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.