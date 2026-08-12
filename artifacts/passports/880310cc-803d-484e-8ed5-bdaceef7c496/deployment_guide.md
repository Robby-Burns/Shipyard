# Production Deployment Guide

Release Tag: rel_880310cc
Commit Hash: ea0c9b666d9b6d17e08b5f212228462e20d7880b
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.