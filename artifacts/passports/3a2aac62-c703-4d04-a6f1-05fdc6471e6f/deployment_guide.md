# Production Deployment Guide

Release Tag: rel_3a2aac62
Commit Hash: d94a28b4ef377f53f7bab94e941e7697768fba38
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.