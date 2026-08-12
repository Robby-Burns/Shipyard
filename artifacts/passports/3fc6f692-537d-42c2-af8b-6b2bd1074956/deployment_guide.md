# Production Deployment Guide

Release Tag: rel_3fc6f692
Commit Hash: 65f2a77663e3b8a383afef11a84ce8a07d32272a
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.