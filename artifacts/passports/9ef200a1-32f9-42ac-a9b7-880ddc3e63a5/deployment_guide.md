# Production Deployment Guide

Release Tag: rel_9ef200a1
Commit Hash: 7ba54b79bf2c3db928afbe2f88ce9e3744916e1b
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.