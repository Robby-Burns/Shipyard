# Production Deployment Guide

Release Tag: rel_882df91c
Commit Hash: 2d8a9ed9200975b86408680d098e23c475baadb2
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.