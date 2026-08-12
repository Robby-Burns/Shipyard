# Production Deployment Guide

Release Tag: rel_3240e2f4
Commit Hash: bfbd4216401d874e4b39387100596b74e88648af
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.