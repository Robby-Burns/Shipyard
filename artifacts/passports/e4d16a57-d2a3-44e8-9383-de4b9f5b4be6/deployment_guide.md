# Production Deployment Guide

Release Tag: rel_e4d16a57
Commit Hash: 177d1bb18205efdf7cf41344c81e51c33796c792
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.