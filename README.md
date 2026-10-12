# Helios — Distributed LLM Gateway

Helios is a gateway that sits between applications and LLM providers (Groq, Gemini). It authenticates and rate-limits requests, answers repeated or similar questions from a cache instead of calling an LLM, routes the rest to a suitable provider, and automatically fails over when a provider is down. It comes with a React admin console, a PostgreSQL database, and Prometheus/Grafana monitoring.

## Architecture

![Helios architecture](docs/architecture.svg)

```
Browser (React UI) ──► nginx ──► FastAPI backend ──► Groq / Gemini
                                   │   │   │
                                   │   │   └─► PostgreSQL (providers, API keys, request logs)
                                   │   └─────► Redis (exact cache, rate limits)
                                   └─────────► Prometheus ──► Grafana
```

### Request pipeline

1. **Auth** — the API key is checked against the database.
2. **Rate limit** — per-key counter in Redis (fixed 60-second window).
3. **Exact cache** — a SHA-256 of the normalized prompt is looked up in Redis.
4. **Semantic cache** — if there is no exact match, the prompt is embedded with `all-MiniLM-L6-v2` and compared by cosine similarity (threshold 0.75) with previously answered prompts.
5. **Router** — an LLM-based classifier picks the best provider for the task.
6. **Circuit breaker + failover** — each provider has a circuit breaker (closed / open / half-open, 3 failures, 30 s cooldown). If the chosen provider is unavailable, the next one in the fallback order is tried.
7. **Save** — the answer is stored in Redis (TTL 300 s) and in the semantic index.
8. **Log** — the request is stored in PostgreSQL and exposed through Prometheus metrics.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), served by nginx |
| Backend | Python, FastAPI, Pydantic |
| Database | PostgreSQL 16 (SQLAlchemy) |
| Cache / rate limiting | Redis 7 |
| Semantic search | sentence-transformers (`all-MiniLM-L6-v2`), cosine similarity |
| LLM providers | Groq, Gemini |
| Monitoring | Prometheus, Grafana |
| Packaging | Docker, Docker Compose |
| Testing | pytest, Locust (load testing) |

## Running it

**Requirements:** Docker Desktop (with at least 4 GB of memory available to Docker).

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your Groq and Gemini API keys and the gateway API key.
3. Start everything:
```
   docker compose up --build
```
   The first build takes a while because of PyTorch.
4. In a second terminal, add the provider rows to the database (once):
```
   docker compose exec -e PYTHONPATH=/app app python scripts/seed_providers.py
```
5. Open the UI, go to **API Keys**, create a key, then try it in the **Playground**.

| What | URL |
|---|---|
| Admin UI | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/docs |
| Prometheus metrics | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin / admin) |

## Admin UI

- **Playground** — send a prompt and watch it pass through each pipeline stage, with cache hits, provider and latency shown.
- **Logs** — every request stored in PostgreSQL.
- **Dashboard** — request counts, cache hit rate, latency and traffic per provider, computed from the logs.
- **Providers** — the configured providers and their health.
- **API Keys** — create, disable and delete keys.

## Monitoring

Prometheus scrapes `/metrics` from the backend. The Grafana dashboard *Helios Overview* shows requests by `cache_result` (`hit_exact`, `hit_semantic`, `miss`), latency, and provider failures.

## Testing

Unit tests (run inside Docker):
```
docker compose exec app pytest
```

Load test with Locust (simulated users sending a mix of questions and rewordings):
```
locust -f benchmarks/locustfile.py --host http://localhost:8000
```
Then open http://localhost:8089 and watch Grafana while it runs.

## Known limitations

This is a college project, so these are deliberate trade-offs, listed honestly:

- **No authentication on the admin API** (`/api/*`). The UI is an admin console; it should not be exposed to the public internet as it is.
- **Not OpenAI-compatible.** The gateway has its own request format.
- **Router is an LLM classifier,** not a rule or YAML-based policy engine.
- **Providers are called synchronously** (blocking HTTP calls).
- **Semantic cache index is in memory.** It resets when the backend restarts and is not shared between multiple instances. A vector store would be the next step.
- **Failed requests (for example 401s) are not written to the request log,** so the dashboard's error rate does not reflect them.
- **Ollama support** is wired in the fallback order but untested.
- **Docker image is single-stage,** so it is larger than necessary.

## Project structure

```
app/            FastAPI backend (api, services, cache, resilience, observability, db)
helios-ui/      React admin console + nginx config
benchmarks/     Locust load test
prometheus/     Prometheus config
scripts/        Database seed script
tests/          pytest tests
docs/           Architecture diagram
docker-compose.yml
```
