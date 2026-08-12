# Production Deployment Guide

Release Tag: rel_aad44ed4
Commit Hash: c76cb9ce82b00de3da70662f11429e00b84538e5
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.