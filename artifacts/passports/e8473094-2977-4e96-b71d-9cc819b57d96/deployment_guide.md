# Production Deployment Guide

Release Tag: rel_e8473094
Commit Hash: 7992b6ec2be34c9a45de5fda0419a454340c36b0
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.