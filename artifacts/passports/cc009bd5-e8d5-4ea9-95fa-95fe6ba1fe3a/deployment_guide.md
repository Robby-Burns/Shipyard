# Production Deployment Guide

Release Tag: rel_cc009bd5
Commit Hash: fa589d1dd3f50686d832ec2ad4dc238ac0dfa2cf
Steps:
1. Pull the repository branch containing the commit.
2. Run database migrations: `alembic upgrade head`.
3. Run healthchecks: `/healthz` and `/readyz`.
4. Verify application operations.