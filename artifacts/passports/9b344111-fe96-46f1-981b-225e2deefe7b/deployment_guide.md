# Production Deployment Guide

Release Tag: rel_9b344111
Commit Hash: 180aeb443253f2dadb29fc0549a245956330a675
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.