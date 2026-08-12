# Production Deployment Guide

Release Tag: rel_d6767414
Commit Hash: 7e4918158568f953caf4ac7f710c879ba47fa7de
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.