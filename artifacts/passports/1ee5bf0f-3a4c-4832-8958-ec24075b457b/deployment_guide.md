# Production Deployment Guide

Release Tag: rel_1ee5bf0f
Commit Hash: 0bed68d93f5deb2866e1dd6083f0f892da301761
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.