# Production Deployment Guide

Release Tag: rel_8a14314d
Commit Hash: 592e91cc92e0fa12da191a03f0b10154adc602d6
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.