# Production Deployment Guide

Release Tag: rel_8800f707
Commit Hash: f4efad0a07a5f055714a8f011fa9c5dcec05da00
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.