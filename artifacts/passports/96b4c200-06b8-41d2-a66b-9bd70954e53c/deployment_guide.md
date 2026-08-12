# Production Deployment Guide

Release Tag: rel_96b4c200
Commit Hash: d3a8a2a09a2f07be2b1b78a59d1a59075f067c10
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.