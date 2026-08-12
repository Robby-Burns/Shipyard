# Production Deployment Guide

Release Tag: rel_e41f53ce
Commit Hash: bb3e5d3545a9bbcafa82ba53b69aad1547062aac
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.