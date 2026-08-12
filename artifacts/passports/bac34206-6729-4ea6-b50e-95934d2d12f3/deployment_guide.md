# Production Deployment Guide

Release Tag: rel_bac34206
Commit Hash: 4ae897e571a25915ad990eb91b4825aa85a38449
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.