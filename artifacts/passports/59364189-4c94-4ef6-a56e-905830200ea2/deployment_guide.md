# Production Deployment Guide

Release Tag: rel_59364189
Commit Hash: 14e04bb63c9c06a4a875fa755cac2bcf9ed38ab3
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.