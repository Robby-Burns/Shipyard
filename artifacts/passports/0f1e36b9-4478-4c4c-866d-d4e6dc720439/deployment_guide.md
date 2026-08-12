# Production Deployment Guide

Release Tag: rel_0f1e36b9
Commit Hash: b71dabd6ab9cb746f1dc3ab7c032e49911f624ab
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.