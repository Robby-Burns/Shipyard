# Production Deployment Guide

Release Tag: rel_9fe19a2a
Commit Hash: 494d8d1c54b59d7ab439b75caace3f12f76c2cea
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.