# Production Deployment Guide

Release Tag: rel_632e9c28
Commit Hash: d168ac2a97e599d4174fa2fb4114e5f12e9358fd
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.