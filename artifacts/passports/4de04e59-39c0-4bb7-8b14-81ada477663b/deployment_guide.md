# Production Deployment Guide

Release Tag: rel_4de04e59
Commit Hash: f7703020649be7b3a7ced97828a7d5ea749a67e3
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.