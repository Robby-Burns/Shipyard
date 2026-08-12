# Production Deployment Guide

Release Tag: rel_f639d026
Commit Hash: 237a2977bebe5dde0cea4dacdc80dd57d854955e
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.