# Production Deployment Guide

Release Tag: rel_b52e80e9
Commit Hash: 9d00514b511c5e8e664299c3d88d2aad2107e9fd
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.