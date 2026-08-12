# Production Deployment Guide

Release Tag: rel_bc1d055c
Commit Hash: ee18faa6142af23c8a9b5e031cc7d896c3efc81c
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.