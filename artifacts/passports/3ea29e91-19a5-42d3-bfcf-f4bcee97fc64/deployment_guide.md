# Production Deployment Guide

Release Tag: rel_3ea29e91
Commit Hash: e04070531ae5d9cca9587aef3acb503597a861d0
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.