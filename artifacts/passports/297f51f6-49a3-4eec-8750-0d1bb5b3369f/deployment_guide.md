# Production Deployment Guide

Release Tag: rel_297f51f6
Commit Hash: 4fc50adec8a7ab801eb95731acba29f4b5f551d3
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.