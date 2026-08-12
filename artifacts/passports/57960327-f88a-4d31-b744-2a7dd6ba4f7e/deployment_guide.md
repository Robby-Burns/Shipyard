# Production Deployment Guide

Release Tag: rel_57960327
Commit Hash: 90b7bc04c0e8b30bb027fa3dbc8a358c94bfd6e4
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.