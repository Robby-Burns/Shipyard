# Production Deployment Guide

Release Tag: rel_fe78c8dc
Commit Hash: ff74af5bf5ac406e3c9c5d59c91ebf3289de3d92
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.