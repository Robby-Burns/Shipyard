# Production Deployment Guide

Release Tag: rel_7b402f13
Commit Hash: f20d18d69c922cf44918755effddeaf5dc26f4f4
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.