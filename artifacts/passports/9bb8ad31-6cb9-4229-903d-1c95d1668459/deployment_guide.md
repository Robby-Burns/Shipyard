# Production Deployment Guide

Release Tag: rel_9bb8ad31
Commit Hash: 60a6ac985b8d0971c32f1f27b3d3b7c54ed29636
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.