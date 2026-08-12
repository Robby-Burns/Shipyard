# Production Deployment Guide

Release Tag: rel_520d676d
Commit Hash: a794d8f8b57b5200502a24281961c6467b31386e
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.