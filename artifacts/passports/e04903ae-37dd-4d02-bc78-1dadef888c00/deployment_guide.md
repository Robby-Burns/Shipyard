# Production Deployment Guide

Release Tag: rel_e04903ae
Commit Hash: 17f868d599d818a08b7baff7f4fd27d0efab3f62
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.