# Production Deployment Guide

Release Tag: rel_bfc3617f
Commit Hash: 960b9c84b885a0c6d2ab872ba3990f954864e26e
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.