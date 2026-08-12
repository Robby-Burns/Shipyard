# Production Deployment Guide

Release Tag: rel_2680bd36
Commit Hash: 4be4f16d3d11419ac065ccca99d5c477c363ef6d
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.