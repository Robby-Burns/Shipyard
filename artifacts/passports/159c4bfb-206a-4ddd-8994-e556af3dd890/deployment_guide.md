# Production Deployment Guide

Release Tag: rel_159c4bfb
Commit Hash: 38c2e90e6fdaf52671873deea6af260f820d7062
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.