# Production Deployment Guide

Release Tag: rel_74ddf256
Commit Hash: b97b2d9deb8dd0bd960336179bed7fc106971175
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.