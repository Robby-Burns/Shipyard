# Production Deployment Guide

Release Tag: rel_c2dc775a
Commit Hash: fe4de682033fe6b97dd63574ea64051113fbdec9
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.