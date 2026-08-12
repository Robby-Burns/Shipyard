# Production Deployment Guide

Release Tag: rel_0e55dee8
Commit Hash: 1f12ded9e07d42a2db2658eb19653d52791ec519
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.