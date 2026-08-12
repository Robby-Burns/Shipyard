# Production Deployment Guide

Release Tag: rel_8650e063
Commit Hash: 920edc2aa21f3d77e59f28ec940d7c2ed1002223
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.