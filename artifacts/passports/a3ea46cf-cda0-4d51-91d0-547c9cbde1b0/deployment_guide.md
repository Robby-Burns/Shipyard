# Production Deployment Guide

Release Tag: rel_a3ea46cf
Commit Hash: ddb8f6150be231d6fe3dbba6851f76f202f3f31d
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.