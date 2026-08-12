# Production Deployment Guide

Release Tag: rel_aba68f0e
Commit Hash: 37eb44aa11203de45aacd1438999f964a3f8a392
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.