# Production Deployment Guide

Release Tag: rel_7a46ed03
Commit Hash: abb01a361c5ca29dd87b21ff494122f4d45f837d
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.