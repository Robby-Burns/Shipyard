# Production Deployment Guide

Release Tag: rel_c1e78a87
Commit Hash: 77dd89c2fa3329dba50d4097136352c29d17022f
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.