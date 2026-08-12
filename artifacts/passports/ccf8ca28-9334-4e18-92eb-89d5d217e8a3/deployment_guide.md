# Production Deployment Guide

Release Tag: rel_ccf8ca28
Commit Hash: d0356b563098f618e7650a1805306877facef756
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.