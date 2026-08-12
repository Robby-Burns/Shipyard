# Production Deployment Guide

Release Tag: rel_a40464e9
Commit Hash: f3d1be749871903d6ea13f2e6271a0ac43a6429d
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.