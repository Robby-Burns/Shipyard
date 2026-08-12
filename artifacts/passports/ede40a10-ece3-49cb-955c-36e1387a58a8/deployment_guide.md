# Production Deployment Guide

Release Tag: rel_ede40a10
Commit Hash: 66c01cc3316657611766d0e501d20e153e452abc
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.