# Production Deployment Guide

Release Tag: rel_d17ca1a7
Commit Hash: a4925d14b0bbfda21c6e6306baafb0b9ef28f41a
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.