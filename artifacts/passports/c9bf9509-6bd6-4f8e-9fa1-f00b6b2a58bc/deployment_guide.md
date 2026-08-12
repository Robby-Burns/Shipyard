# Production Deployment Guide

Release Tag: rel_c9bf9509
Commit Hash: ad325ab67d7a7e63c88d9a7bd418b42742170c62
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.