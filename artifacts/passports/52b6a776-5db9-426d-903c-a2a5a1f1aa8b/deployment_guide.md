# Production Deployment Guide

Release Tag: rel_52b6a776
Commit Hash: 1c099bbe5512c68cef0b9db5ff68fdaf6509f1df
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.