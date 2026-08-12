# Production Deployment Guide

Release Tag: rel_285f6598
Commit Hash: 632aa10e8bd59a955a3c7de153f9c5f7b999d1ef
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.