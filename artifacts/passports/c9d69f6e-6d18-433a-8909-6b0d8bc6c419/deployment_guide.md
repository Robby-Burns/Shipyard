# Production Deployment Guide

Release Tag: rel_c9d69f6e
Commit Hash: dba62f3537010029eba18986388a47581a81b232
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.