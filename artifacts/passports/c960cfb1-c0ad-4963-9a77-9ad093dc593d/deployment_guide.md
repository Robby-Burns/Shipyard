# Production Deployment Guide

Release Tag: rel_c960cfb1
Commit Hash: 95ee80892e15eac3699fac6fc5656431bdc6fc81
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.