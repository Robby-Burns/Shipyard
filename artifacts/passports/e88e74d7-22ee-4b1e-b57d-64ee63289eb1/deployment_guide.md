# Production Deployment Guide

Release Tag: rel_e88e74d7
Commit Hash: a50036d35cd2c8f2862958d8be6618397e42bd15
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.