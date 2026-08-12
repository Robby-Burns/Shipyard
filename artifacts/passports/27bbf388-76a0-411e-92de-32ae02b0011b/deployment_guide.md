# Production Deployment Guide

Release Tag: rel_27bbf388
Commit Hash: 752a5cd571319f49336da5c559d2fa215f335fcd
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.