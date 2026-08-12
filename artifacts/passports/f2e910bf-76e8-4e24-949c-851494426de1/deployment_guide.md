# Production Deployment Guide

Release Tag: rel_f2e910bf
Commit Hash: ccf17718db7e8cb444b64a18d1139cf780e9be38
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.