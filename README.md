# Messenger Backend Playground 🧪

> A fun backend lab where messaging, architecture, and async ideas get tested in public.

This repository is a backend playground for experimenting with messaging systems, architecture patterns, and async workflows.

It is not just a single "send message" API. It is a space to learn, break things safely, and evolve ideas 😄

Think of it as an engineering sandbox where I test concepts in real code.

One of the main goals here is learning how software is structured in enterprise-style systems (layered architecture, clear boundaries, async workflows, and integration-heavy design).

- hexagonal/clean-ish architecture with clear ports and adapters
- pluggable messenger providers (Telegram, WhatsApp)
- outbox pattern + background workers + optional broker mode
- bulk import pipelines (CSV/XLSX) with staging and processing steps
- dependency injection, unit-of-work boundaries, and domain events

## What this project does

At a high level, this backend lets you:

- authenticate users and manage sessions
- connect messenger sessions (OTP/password for Telegram, QR for WhatsApp)
- upload files to S3/MinIO
- create message requests and generate messages from tabular files
- dispatch those messages asynchronously through workers
- switch event dispatch from direct DB worker handling to broker-based handling (RabbitMQ implemented now)

Learning-first note: this project intentionally favors experimentation over polish in some areas, so multiple approaches may coexist while ideas are being compared.

## Why this is cool ✨

- You can plug in messenger providers behind the same core use cases.
- You can switch async dispatch style (`direct` vs `broker`) without rewriting domain logic.
- You can run workers as loops **or** one-shot jobs (`--once`) for CronJob-style scheduling.
- You can explore enterprise-style patterns in a project that is still playful and fast to change.

## Architecture at a glance 🏗️

The code is organized by bounded context and layer:

- `app/`: FastAPI entrypoints, routers, DI wiring, runtime composition
- `src/base/`: shared abstractions (ports, UoW, outbox, worker plumbing)
- `src/users/`: auth/user models, repos, JWT/password adapters
- `src/files/`: file domain + S3/MinIO integration
- `src/messaging/`: messenger domain, providers, use cases, workers
- `src/importing/`: generic import framework (staging/process/config/handlers)
- `migrations/`: Alembic migrations

### Runtime flow (simplified)

```text
Client -> FastAPI routes (app/) -> Use cases (src/*/application)
      -> Unit of Work (SQLAlchemy repos)
      -> Outbox event persisted in DB
      -> Worker dispatches event
           -> direct mode: execute handler now
           -> broker mode: publish to event bus, consumer executes handler
```

```text
API Request -> DB write -> Outbox row -> Worker tick -> Handler/Bus -> Message send
```

### Main architectural parts

1. API layer (`app/main.py`, `app/v1/**`)
   - HTTP contracts, request validation, auth dependency hooks
   - very thin endpoints that call application use cases

2. Dependency Injection (`app/container.py`)
   - central composition root using `dependency-injector`
   - selects implementations for DB, cache, messengers, event bus, imports

3. Domain/Application core (`src/**/application`, `src/**/domain`)
   - entities and use cases are isolated from framework details
   - ports define what infrastructure should provide

4. Infrastructure adapters (`src/**/adapters`)
   - SQLAlchemy repos, Redis cache/staging, S3 file service
   - Telegram via Telethon, WhatsApp via Evolution API HTTP adapter

5. Async orchestration (`app/workers.py`, `app/consumer.py`)
   - polling workers for outbox and CSV generation
   - broker consumer abstraction supports different buses; RabbitMQ is the current implementation

## Playground ideas currently in the code 🎯

These are the "experiments" this repo currently contains:

- **Pluggable messengers with capability discovery**
  - messenger descriptors infer features/auth/contact methods from interfaces
  - supports multiple auth styles and contact identifiers per provider

- **Dual outbox dispatch strategy**
  - `outbox_dispatch_strategy=direct`: DB worker executes handlers directly
  - `outbox_dispatch_strategy=broker`: worker publishes to event bus, consumer handles

- **Event bus abstraction (pluggable consumers/brokers)**
  - architecture is designed for multiple bus implementations (e.g., RabbitMQ, Kafka, others)
  - current concrete implementation is RabbitMQ

- **Outbox reliability mechanisms**
  - retry attempts with exponential backoff
  - dead-letter behavior after max attempts
  - dedup/aggregate metadata kept on outbox rows

- **Two message-generation paths**
  - generic import pipeline (stage -> process) with typed configs

- **Import framework as reusable engine**
  - import registry maps `import_type` to config + handler
  - tabular resolver supports multiple readers (`.csv`, `.xlsx`)
  - unknown column policies, row-level error capture, staged row processing

- **UoW and repository boundaries**
  - explicit transactional boundaries in use cases and workers
  - clear separation of write-side repositories and read-side queries

## API surface (current) 📡

Base:

- `GET /` health/root

V1:

- Users/Auth:
  - `POST /v1/users/auth/login`
  - `GET /v1/users/auth/current_user`
- Files:
  - `POST /v1/files/upload`
  - `GET /v1/files/{file_id}`
- Messaging:
  - `POST /v1/messaging/message`
  - `POST /v1/messaging/message-requests/csv`
  - `POST /v1/messaging/message-requests/import`
  - `GET /v1/messaging/message-requests/{message_request_id}`
- Session/Messenger discovery + auth:
  - `GET /v1/messaging/sessions/messengers`
  - `POST /v1/messaging/sessions/otp`
  - `POST /v1/messaging/sessions/qr`
  - `POST /v1/messaging/sessions/verify/opt` (spelled this way in current route)
  - `POST /v1/messaging/sessions/verify/password`

Interactive docs are available at `/docs` when the app is running.

## Running 🚀

### Development (`docker-compose-dev.yml`)

Use this profile for local experimentation. It boots infrastructure services and keeps the backend workflow flexible for local `uvicorn`/worker runs.

1. Copy env template:

```bash
cp sample.env .env
```

2. Start dev infra:

```bash
docker compose -f docker-compose-dev.yml up -d
```

3. Run app locally:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Development setup intent:

- run infrastructure in Docker
- run API/workers locally
- keep feedback loops fast during development

### Production-like (`docker-compose.yml`)

Use this profile to run a fuller stack closer to deployment shape (backend API + workers + consumer + infra in containers).

```bash
cp sample.env .env
docker compose -f docker-compose.yml up --build
```

Run migrations (if needed):

```bash
docker compose -f docker-compose.yml run --rm backend uv run alembic upgrade head
```

Open:

- API docs: `http://localhost:8000/docs`
- MinIO console: `http://localhost:9001`
- RabbitMQ UI: `http://localhost:15672` (when exposed in your compose)

Run workers separately as needed:

```bash
uv run python -m app.workers --job dispatch_outbox_events
```

Workers also support one-shot execution via `--once`, so they can run as scheduled jobs (for example Kubernetes CronJobs) instead of only long-running loops:

```bash
uv run python -m app.workers --job dispatch_outbox_events --once
```

Run broker consumer (only when broker is enabled, i.e. `broker_driver` is not `none`):

```bash
uv run python -m app.consumer
```

## Important configuration toggles

In `.env`:

- `outbox_dispatch_strategy=direct|broker`
- `broker_driver=none|rabbitmq`
- `broker_url=amqp://...`
- messenger credentials (`telegram_*`, `whatsapp_*`)
- storage and infra values (database, redis, s3/minio)

## Learning goals in this repo 🧠

- Understand how enterprise-style backend boundaries look in practice.
- Practice event-driven workflows with outbox + workers + optional bus.
- Compare simple and advanced import pipelines side by side.
- Keep experimenting without losing architectural clarity.

## Why this repo exists ❤️

This codebase is intentionally a **playground**.

It is where different backend concepts are tried in real code, compared against each other, and incrementally refactored. Some flows are intentionally overlapping (for example CSV worker path vs import pipeline) because the point is to explore trade-offs and learn by building.

This is a fun learning lab first, production template second 🚀

Think of this project as a lab for:

- architecture experiments
- event-driven workflow design
- integration patterns for external messaging systems
- practical async + worker reliability patterns

## Notes

- Python requirement is `>=3.13`.
- Uses `uv` for dependency/project management.
