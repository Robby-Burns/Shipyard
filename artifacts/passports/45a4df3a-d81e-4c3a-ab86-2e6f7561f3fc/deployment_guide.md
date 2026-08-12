# Production Deployment Guide

Release Tag: rel_45a4df3a
Commit Hash: 1061dd36e29fd62895bd6736481defb3a5aac9ee
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.