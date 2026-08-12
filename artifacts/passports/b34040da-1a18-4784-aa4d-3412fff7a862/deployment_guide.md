# Production Deployment Guide

Release Tag: rel_b34040da
Commit Hash: ccbbb157e6cc3ff480ac564fd1479e524cc7da87
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.