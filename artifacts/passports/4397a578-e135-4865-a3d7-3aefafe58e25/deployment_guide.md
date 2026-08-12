# Production Deployment Guide

Release Tag: rel_4397a578
Commit Hash: 73ee8cfa98abb001b65957fe07bc6cccbe108c48
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.