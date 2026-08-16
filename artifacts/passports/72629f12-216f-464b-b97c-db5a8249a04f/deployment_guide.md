# Production Deployment Guide

Release Tag: rel_72629f12
Commit Hash: 8f688667d3f9f9e4bb84174c7ffc9715b1b5e4a9
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.