# Production Deployment Guide

Release Tag: rel_b16b5e01
Commit Hash: fab158ce3591f041d9c9899dc9dc5f0a3b9c40a2
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.