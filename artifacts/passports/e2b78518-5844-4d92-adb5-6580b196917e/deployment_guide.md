# Production Deployment Guide

Release Tag: rel_e2b78518
Commit Hash: efb13931e38118854678e2a8c58d8a9cd4acb801
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.