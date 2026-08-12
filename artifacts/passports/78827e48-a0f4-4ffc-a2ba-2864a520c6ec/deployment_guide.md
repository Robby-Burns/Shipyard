# Production Deployment Guide

Release Tag: rel_78827e48
Commit Hash: 0c15123df34003ec8ea2df43da0af5ed63d02d02
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.