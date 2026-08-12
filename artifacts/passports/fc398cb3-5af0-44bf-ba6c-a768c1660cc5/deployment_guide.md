# Production Deployment Guide

Release Tag: rel_fc398cb3
Commit Hash: 041422cf34c402d10100d7c1d3af76cbfac7bdec
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.