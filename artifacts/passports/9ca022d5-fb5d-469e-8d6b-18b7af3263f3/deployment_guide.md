# Production Deployment Guide

Release Tag: rel_9ca022d5
Commit Hash: 615be6d57dff5a6b45bdd78e01512e574a926d65
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.