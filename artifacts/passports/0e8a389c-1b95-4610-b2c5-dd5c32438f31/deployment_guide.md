# Production Deployment Guide

Release Tag: rel_0e8a389c
Commit Hash: de229a865a5f110b86888953a17f9fb6cb2a4498
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.