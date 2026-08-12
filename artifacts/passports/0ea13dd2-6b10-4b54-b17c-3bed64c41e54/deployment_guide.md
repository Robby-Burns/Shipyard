# Production Deployment Guide

Release Tag: rel_0ea13dd2
Commit Hash: a77b547566aa77aed6f1328616f081bd93c2cc22
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.