# Production Deployment Guide

Release Tag: rel_16cb4fdd
Commit Hash: 223313303b6b4ebb36b7f35fbd0982279ffcbeb9
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.