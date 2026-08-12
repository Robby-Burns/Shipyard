# Production Deployment Guide

Release Tag: rel_65940a4b
Commit Hash: 66f46e9c232291d19f833e5eb27b7bb5a7c8766b
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.