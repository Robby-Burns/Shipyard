# Production Deployment Guide

Release Tag: rel_28a1aa7b
Commit Hash: 1504011a21270a953d8a2c981ef7123bf65fe1e6
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.