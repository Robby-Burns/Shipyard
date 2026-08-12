# Production Deployment Guide

Release Tag: rel_2bf5b20d
Commit Hash: ee3ecaedb4f61f5d6ad8d9469e72f58f95027ae0
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.