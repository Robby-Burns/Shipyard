# Shipyard Platform

[![Continuous Integration](https://github.com/Robby-Burns/Shipyard/actions/workflows/ci.yml/badge.svg)](https://github.com/Robby-Burns/Shipyard/actions/workflows/ci.yml)
[![Continuous Deployment](https://github.com/Robby-Burns/Shipyard/actions/workflows/cd.yml/badge.svg)](https://github.com/Robby-Burns/Shipyard/actions/workflows/cd.yml)

Shipyard is a high-performance backend API application built with **FastAPI**, **SQLAlchemy 2.0 (async)**, **Alembic**, and **PostgreSQL (`pgvector`)**.

---

## Features

- **FastAPI Core**: Async RESTful API routes with OpenAPI standard documentation.
- **Database & Migrations**: SQLAlchemy 2.0 async connection pooling with Alembic migration scripts and `pgvector` support.
- **Authentication & Security**: Bearer JWT token verification, CORS configuration, and security headers.
- **Observability**: `structlog` JSON structured logging and request context tracing via `X-Request-ID`.
- **Global Error Handling**: Standardized error response structures for unhandled exceptions and validation errors.
- **Containerization & CI/CD**: Production-ready multi-stage Docker setup, Docker Compose environment, and GitHub Actions pipelines.

---

## Local Setup

### 1. Environment & Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows: source .venv/bin/activate on Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

---

## Database Migrations

Apply database migrations using Alembic:

```bash
alembic upgrade head
```

---

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access API endpoints:
- **Root**: `http://localhost:8000/`
- **Health Check**: `http://localhost:8000/healthz`
- **Readiness Check**: `http://localhost:8000/readyz`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## Running Tests

Run the full pytest suite:

```bash
pytest -v
```

---

## Docker & Docker Compose

### Start Services

```bash
docker compose up --build -d
```

### Apply Migrations in Container

```bash
docker compose exec app alembic upgrade head
```

### Stop Services

```bash
docker compose down
```

---

## CI/CD Pipelines

- **Continuous Integration (`.github/workflows/ci.yml`)**: Automatically runs migrations, pytest unit tests against PostgreSQL (`pgvector`), and validates Docker container image builds on pushes and pull requests to `main`.
- **Continuous Deployment (`.github/workflows/cd.yml`)**: Automates staging/production deployment upon successful CI checks.
