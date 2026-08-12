# Production Deployment Guide

Release Tag: rel_6eacb16e
Commit Hash: e02f1a1a67dc89509bb08f9c16618dbbbaab9edc
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.