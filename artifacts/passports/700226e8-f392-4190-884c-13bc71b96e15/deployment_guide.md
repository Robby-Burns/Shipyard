# Production Deployment Guide

Release Tag: rel_700226e8
Commit Hash: 94fa1bcbd0562c28304f52991ab3700beee5264e
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.