# Production Deployment Guide

Release Tag: rel_93ed368e
Commit Hash: 6a1673b865abccbe51948f73fbb7a2f01a997143
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.