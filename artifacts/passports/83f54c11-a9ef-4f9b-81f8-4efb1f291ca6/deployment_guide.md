# Production Deployment Guide

Release Tag: rel_83f54c11
Commit Hash: 8557571a4bd506a0ae785a85f4bc586bfc6fb2ff
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.