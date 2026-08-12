# Production Deployment Guide

Release Tag: rel_dceaaf4e
Commit Hash: 307225616dce070528ec887c804fa45c6bc5fd58
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.