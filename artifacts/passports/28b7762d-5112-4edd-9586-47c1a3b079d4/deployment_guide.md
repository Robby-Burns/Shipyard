# Production Deployment Guide

Release Tag: rel_28b7762d
Commit Hash: 9165191cbece96c8c131ed4358ece8418badfc2b
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.