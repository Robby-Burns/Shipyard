# Production Deployment Guide

Release Tag: rel_ec793578
Commit Hash: 6ac73673dd153dcafe3d28c518fa06a22d832cee
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.