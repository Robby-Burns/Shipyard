# Production Deployment Guide

Release Tag: rel_a3f9e7eb
Commit Hash: d66662b1d0aa4434af17ba76b35a366f0c88d557
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.