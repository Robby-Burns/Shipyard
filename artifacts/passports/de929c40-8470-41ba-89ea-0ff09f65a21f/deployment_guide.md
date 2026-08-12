# Production Deployment Guide

Release Tag: rel_de929c40
Commit Hash: 469a34a3e3a8d1561494baa2c4f9c269a9f5072e
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.