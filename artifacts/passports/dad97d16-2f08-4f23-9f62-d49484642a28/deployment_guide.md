# Production Deployment Guide

Release Tag: rel_dad97d16
Commit Hash: e1cd9ec9a3d3b4fea2c1772d7019b31377b5529d
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.