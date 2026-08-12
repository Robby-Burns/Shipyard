# Production Deployment Guide

Release Tag: rel_35bfde49
Commit Hash: ef62f84629c5ea7a83006115d9eaa4d86e635950
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.