# Production Deployment Guide

Release Tag: rel_248da06c
Commit Hash: 56c146d20663af3de10bf72318fe9334ccad79c3
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.