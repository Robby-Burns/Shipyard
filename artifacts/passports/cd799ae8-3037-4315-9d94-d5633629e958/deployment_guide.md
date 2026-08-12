# Production Deployment Guide

Release Tag: rel_cd799ae8
Commit Hash: c93639abf7f9c70bc5efaeabeb136d1a930a1b44
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.