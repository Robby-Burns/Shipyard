# Production Deployment Guide

Release Tag: rel_c22e1436
Commit Hash: 5efa6e3de3dc482f1bfe69bbd35cb24c5f7650db
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.