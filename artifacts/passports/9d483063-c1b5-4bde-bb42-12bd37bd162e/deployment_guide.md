# Production Deployment Guide

Release Tag: rel_9d483063
Commit Hash: 33cfda34930d88034efb1538fb1f705bda5ea7b0
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.