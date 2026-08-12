# Production Deployment Guide

Release Tag: rel_39d12e35
Commit Hash: 419b714fe742f37c432191792a9a8a9184d88112
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.