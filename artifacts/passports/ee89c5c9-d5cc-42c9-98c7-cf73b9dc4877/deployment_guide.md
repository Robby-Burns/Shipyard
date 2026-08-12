# Production Deployment Guide

Release Tag: rel_ee89c5c9
Commit Hash: 836f6a2ef918d70c19ffa4c7e2723cce30a7f642
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.