# Production Deployment Guide

Release Tag: rel_d816551a
Commit Hash: 03575b074199d75aa54b7959a67977b4566f32bc
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.