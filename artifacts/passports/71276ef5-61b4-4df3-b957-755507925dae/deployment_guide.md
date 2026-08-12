# Production Deployment Guide

Release Tag: rel_71276ef5
Commit Hash: e2bf05bb83e04a961c9a3e72ccdf3944b1c79b3c
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.