# Multi-Tenant Job Scheduling & Workflow Engine

A backend-only system inspired by tools like Airflow and Temporal — users define workflows as DAGs of tasks via API, the system schedules and executes them, tracks state, retries failures, and isolates data per tenant. Built to demonstrate production-grade backend engineering, not just CRUD endpoints.

## What This Project Demonstrates

- Async-first API design at scale
- Multi-tenant data isolation strategies
- Distributed task execution with failure recovery
- Idempotency, rate limiting, and real-time status streaming
- Observability (logs, metrics, traces) as a first-class concern
- Testing against real infrastructure, not mocks

## Core Features

- Submit workflow definitions (JSON/YAML) with task dependencies; the engine resolves execution order server-side
- Background execution via a distributed worker pool, with retry/backoff and dead-letter handling
- Idempotency keys on mutating endpoints so retried requests never double-execute
- Per-tenant rate limiting (token bucket)
- Live job status via WebSockets/SSE
- OAuth2 + JWT auth with refresh token rotation, plus API keys for service-to-service calls
- Full observability stack: structured logs, Prometheus metrics, OpenTelemetry traces

## Tech Stack & Why

### FastAPI — instead of Flask / Django REST Framework
- **Native async support**: FastAPI is built on Starlette/ASGI, so I/O-bound operations (DB calls, worker dispatch, WebSocket streaming) don't block the event loop. Flask is WSGI-based and synchronous by default — bolting on async support (via Flask 2.x's limited async views or `Quart`) is a workaround, not a foundation. For a workflow engine where the whole point is concurrent task orchestration, blocking I/O defeats the purpose.
- **Pydantic-native validation**: request/response schemas are enforced automatically with typed models, which matters a lot when the API surface is "arbitrary user-submitted DAG definitions" — a place where malformed input is the norm, not the exception.
- **Automatic OpenAPI docs**: since this is a platform other services will call (workflows can be triggered by external systems), auto-generated, always-accurate OpenAPI/Swagger docs are a real operational advantage over Flask, where docs are usually a separate maintained artifact (e.g., Flask-RESTX) that drifts from the code.
- **Dependency injection system**: FastAPI's `Depends()` makes it clean to inject DB sessions, current-tenant context, and auth checks per-route without global state — important in a multi-tenant system where "which tenant am I operating as" must be unambiguous on every request.
- **vs. Django REST Framework**: DRF is a great choice for content-heavy, admin-panel-driven apps, but it carries ORM and templating assumptions I don't need here, and its class-based views add ceremony for what is fundamentally a lean, async, service-to-service API.

### PostgreSQL (async via SQLAlchemy 2.0) — instead of MongoDB
- Workflows are inherently **relational**: tasks have dependencies on other tasks, jobs belong to tenants, tenants have quotas. Modeling a DAG's edges and enforcing referential integrity (a task can't depend on a task that doesn't exist) is what a relational DB with foreign keys is for. MongoDB would push that integrity logic into the application layer.
- **Row-level multi-tenancy**: Postgres Row-Level Security (RLS) lets me enforce tenant isolation at the database layer as a backstop, not just in application code — a defense-in-depth argument that's hard to replicate cleanly in Mongo.
- **Transactions**: job state transitions (`pending → running → done/failed`) need ACID guarantees, especially when a state change and a queue message need to happen atomically (outbox pattern). Postgres transactions handle this natively.
- SQLAlchemy 2.0's async engine (`asyncpg` driver) keeps the DB layer non-blocking, matching FastAPI's async model end-to-end.

### Celery / ARQ — instead of running tasks in-process
- Workflow tasks are potentially long-running and must survive API process restarts. In-process background tasks (e.g., FastAPI's `BackgroundTasks`) die with the request process and don't scale horizontally — wrong tool for anything beyond fire-and-forget emails.
- **ARQ** (Redis-based, asyncio-native) is a lighter-weight alternative to Celery worth showing awareness of: it avoids Celery's heavier dependency footprint and integrates naturally with an already-async codebase. Celery is included as the "industry default" option to demonstrate I know when heavier tooling (multiple broker support, mature monitoring via Flower, complex retry/canvas workflows) is justified.
- Redis is chosen as the broker over RabbitMQ for this project because it also doubles as the rate-limiting store and pub/sub layer for live status updates — one less moving part in the infra.

### Alembic — instead of hand-written migrations
- Schema drift across environments is a real production failure mode. Alembic (SQLAlchemy's migration tool) auto-generates migration scripts from model changes and keeps a versioned, reversible history — standard practice for any team-scale backend.

### JWT (OAuth2 password/client-credentials flow) — instead of session cookies
- The API is designed for both human users (dashboard) and service-to-service calls (external systems triggering workflows). JWTs are stateless and work identically for both; session cookies assume a browser client and complicate the API-key/service-account use case.
- Refresh token rotation is implemented to limit the blast radius of a leaked token — a deliberate security tradeoff over long-lived static API keys for user-facing auth.

### OpenTelemetry + Prometheus + structlog — instead of print/basic logging
- A workflow engine's core value proposition is "I can tell you what happened and why it failed." Structured logs (JSON, queryable) plus distributed traces (to follow a single job across API → queue → worker) plus metrics (queue depth, task duration, failure rate) are what make the system operable, not just functional. This is the difference between a toy project and something that reflects how backend systems are actually run in production.

### Docker Compose + GitHub Actions CI (with testcontainers)
- Tests run against real Postgres and Redis instances spun up via `testcontainers`, not mocks — this catches real SQL/transaction bugs that mocked sessions hide. Docker Compose gives a one-command local environment that mirrors CI, avoiding "works on my machine" drift.

## Suggested Repo Structure

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
.github/workflows/ci.yml
```

## Stretch Goals

- Workflow versioning (edit a DAG without breaking in-flight runs)
- Per-tenant resource quotas enforced at the scheduler level
- A minimal admin UI for visualizing DAG execution (even a simple Mermaid.js render of job graphs)

## Getting Started

```bash
docker-compose up -d
alembic upgrade head
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.
