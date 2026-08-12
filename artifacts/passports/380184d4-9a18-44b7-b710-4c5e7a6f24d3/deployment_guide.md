# Production Deployment Guide

Release Tag: rel_380184d4
Commit Hash: 21bad02defc2d5170d3c48fa62ec12cdafb886bd
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.