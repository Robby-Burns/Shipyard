# Production Deployment Guide

Release Tag: rel_c972e36d
Commit Hash: 0794ce39d9455038ba3026ef68f5de7aaf3412b0
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.