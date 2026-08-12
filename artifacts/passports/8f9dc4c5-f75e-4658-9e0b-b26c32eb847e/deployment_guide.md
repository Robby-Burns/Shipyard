# Production Deployment Guide

Release Tag: rel_8f9dc4c5
Commit Hash: 72cd431d340c9c9fc9dc826725a5becca25f7593
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.