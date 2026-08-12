# Production Deployment Guide

Release Tag: rel_53571a03
Commit Hash: 4fba7e08f6e426af673107ced43741e8eb67525e
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.