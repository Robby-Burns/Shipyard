# Production Deployment Guide

Release Tag: rel_ca911439
Commit Hash: a3c7e42496ea699b70ccb99b08a1a91a19799cf5
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.