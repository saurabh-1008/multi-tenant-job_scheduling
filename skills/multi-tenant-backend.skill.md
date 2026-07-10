---
name: multi-tenant-backend
description: Multi-Tenant Job Scheduling & Workflow Engine — an async-first, production-grade backend built with FastAPI, PostgreSQL, Celery/ARQ, and full observability stack.
---

# Multi-Tenant Backend Project

## Architecture Overview

This is an async-first backend system for defining, scheduling, and executing workflow DAGs with per-tenant isolation.

## Tech Stack

| Layer        | Technology                          |
|-------------|-------------------------------------|
| API         | FastAPI (Starlette/ASGI)            |
| Database    | PostgreSQL via SQLAlchemy 2.0 async |
| Queue       | Celery / ARQ with Redis broker      |
| Migrations  | Alembic                             |
| Auth        | OAuth2 + JWT with refresh rotation  |
| Rate Limit  | Token bucket (Redis-backed)         |
| Observability | OpenTelemetry + Prometheus + structlog |
| Infra       | Docker Compose + GitHub Actions CI  |

## Directory Structure

```
app/
  api/            # FastAPI routers (workflows, jobs, tenants, auth)
  core/           # config, security, dependency wiring
  db/             # SQLAlchemy models, session management
  scheduler/      # DAG resolution and execution logic
  workers/        # Celery/ARQ task handlers
  observability/  # logging, metrics, tracing setup
tests/
  integration/    # testcontainers-based DB/Redis tests
  unit/
alembic/
docker-compose.yml
```

## Key Design Decisions

- **FastAPI over Flask/DRF**: native async, Pydantic validation, automatic OpenAPI
- **PostgreSQL over MongoDB**: relational DAG models, RLS for tenant isolation, ACID transactions
- **ARQ/Celery over in-process tasks**: survive restarts, scale horizontally
- **JWT over sessions**: stateless, works for human users and service-to-service calls
- **Testcontainers over mocks**: catch real SQL/transaction bugs

## Getting Started

```bash
docker-compose up -d
alembic upgrade head
uvicorn app.main:app --reload
```

## Stretch Goals

- Workflow versioning
- Per-tenant resource quotas
- Minimal admin UI with Mermaid.js DAG visualization
