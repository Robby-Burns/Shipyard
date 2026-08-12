# Production Deployment Guide

Release Tag: rel_eea7d88d
Commit Hash: d15e138ba66628dc1d3a967a5154e711acc39019
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.