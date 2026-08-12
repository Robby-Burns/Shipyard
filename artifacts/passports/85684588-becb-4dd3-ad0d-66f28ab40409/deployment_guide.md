# Production Deployment Guide

Release Tag: rel_85684588
Commit Hash: 6b9059f263b8e63bc48a8686f651ea7477f1a4c4
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.