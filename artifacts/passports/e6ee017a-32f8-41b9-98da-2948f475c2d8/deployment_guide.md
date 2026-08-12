# Production Deployment Guide

Release Tag: rel_e6ee017a
Commit Hash: 65b4ae5ebef25033fa1f2494288ace06512797b5
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.