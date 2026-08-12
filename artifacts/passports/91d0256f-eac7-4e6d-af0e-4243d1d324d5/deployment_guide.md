# Production Deployment Guide

Release Tag: rel_91d0256f
Commit Hash: f5dc612dab27407430e98e41804e6f767905e601
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.