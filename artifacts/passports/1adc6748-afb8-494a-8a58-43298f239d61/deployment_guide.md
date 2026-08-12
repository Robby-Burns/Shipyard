# Production Deployment Guide

Release Tag: rel_1adc6748
Commit Hash: fd2219d7cb748b1f5d2f88fc07dbc7e17916234f
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.