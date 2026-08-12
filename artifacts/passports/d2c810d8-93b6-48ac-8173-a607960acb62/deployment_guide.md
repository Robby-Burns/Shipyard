# Production Deployment Guide

Release Tag: rel_d2c810d8
Commit Hash: b43741c42feb623a1dd83c5940f0fa7a644c2cd4
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.