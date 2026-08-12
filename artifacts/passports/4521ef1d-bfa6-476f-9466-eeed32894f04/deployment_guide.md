# Production Deployment Guide

Release Tag: rel_4521ef1d
Commit Hash: fc890b675e27e4c0bf5b199f634dd74eebe2eb2e
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.