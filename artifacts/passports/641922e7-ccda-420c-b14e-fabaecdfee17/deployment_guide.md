# Production Deployment Guide

Release Tag: rel_641922e7
Commit Hash: 91e0a54088eb016116a2caa01496113d33d81427
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.