# Production Deployment Guide

Release Tag: rel_8cb5d3b7
Commit Hash: 3377abdd22381ff0cbd2bd1ce084ac01048ce64c
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.