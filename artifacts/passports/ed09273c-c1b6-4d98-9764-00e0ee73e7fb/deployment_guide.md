# Production Deployment Guide

Release Tag: rel_ed09273c
Commit Hash: c602b6c8697a427cef19cce0e196dbc16c576f9f
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.