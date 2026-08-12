# Production Deployment Guide

Release Tag: rel_d47b7918
Commit Hash: f0e6c749d24a68c65870360894528108de9955e2
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.