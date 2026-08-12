# Production Deployment Guide

Release Tag: rel_1fc04f5b
Commit Hash: 5b094fc74a0513d75c53681e8be4f48a0bf77d09
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.