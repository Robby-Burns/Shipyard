# Production Deployment Guide

Release Tag: rel_a54b31a7
Commit Hash: 962f230cb5af8a9d6d2e8045f6464e00cd8f80ec
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.