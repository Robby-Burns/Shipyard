# Production Deployment Guide

Release Tag: rel_8d37f2b4
Commit Hash: 91b0894d7720f372676b4aa9ca90a54bc1d6276b
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.