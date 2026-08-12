# Production Deployment Guide

Release Tag: rel_382db8cb
Commit Hash: d459af44e81e12c6e6c39fab76fb079642d39d1f
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.