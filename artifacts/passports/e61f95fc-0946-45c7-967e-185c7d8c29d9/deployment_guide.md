# Production Deployment Guide

Release Tag: rel_e61f95fc
Commit Hash: 07a7ce24435b36631fa3ddbdc3fdc3a2d50deaff
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.