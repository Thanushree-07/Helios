
### Request pipeline

Every request flows through 7 stages:

1. **Auth** — validates `X-API-Key` header → 401 if missing/invalid
2. **Rate limit** — per-client request cap via Redis → 429 if exceeded
3. **Exact cache check** — SHA-256 hash of the prompt → instant return on hit
4. **Semantic cache check** — local embedding similarity (sentence-transformers) catches *reworded* questions an exact match would miss
5. **Router** — an LLM classifies the prompt (task type + complexity) and selects a provider
6. **Circuit breaker + call** — each provider has an independent health tracker (Closed → Open → Half-Open); a failing provider is automatically skipped and the request fails over to the next one
7. **Save + observe** — response cached in Redis (and indexed semantically), Prometheus metrics recorded

## Features

- ✅ Multi-provider routing (Groq, Gemini, Ollama) via an LLM-based classifier
- ✅ Two-tier caching: exact-match (Redis) + semantic similarity (local embeddings, zero API cost)
- ✅ Per-provider circuit breaker with automatic failover — survives real provider outages
- ✅ Per-client rate limiting
- ✅ Full observability: Prometheus metrics + live Grafana dashboard
- ✅ One-command deployment via Docker Compose
- ✅ Automated test suite (pytest) covering auth, caching, and circuit-breaker state transitions
- ✅ Load-tested with Locust

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Uvicorn |
| Cache + rate limiting | Redis |
| Semantic cache | sentence-transformers (all-MiniLM-L6-v2), runs 100% locally |
| LLM providers | Groq, Google Gemini, Ollama |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Containerization | Docker + Docker Compose |
| Testing | pytest |
| Load testing | Locust |

## Quick Start

```bash
git clone <your-repo-url>
cd helios
cp .env.example .env
# fill in your GROQ_API_KEY, GEMINI_API_KEY, and API_KEY in .env

docker compose up --build
```

Once running:
- API docs: `http://localhost:8000/docs`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (default login: admin/admin)

## Usage

```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: your-key-here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python used for?"}'
```

## Benchmark Results

Measured via Locust (10 concurrent simulated users, mixed new/repeated/paraphrased traffic):

| Metric | Result |
|---|---|
| Median latency | 54 ms |
| p95 latency | 230 ms |
| p99 latency | 37,000 ms (provider-outage retries) |
| Failure rate | 1.4% |
| Cache hit rate (test traffic) | ~97%* |
| Semantic vs. exact cache hit, measured example | "What causes earthquakes?" vs "Why do earthquakes happen?" → matched at 0.913 similarity |

\* *This figure reflects Locust's repeated test question pool, not real-world traffic diversity — included for transparency on test methodology, not as a general production claim.*

**Real incident, caught live:** Gemini's free tier returned a genuine `503 Service Unavailable` mid-testing. The circuit breaker recorded the failure and automatically failed over to Groq — the end user never saw an error.

## Testing

```bash
pip install -r requirements.txt
pytest -v
```
11 tests covering authentication, the full `/chat` request flow (mocked providers), and all circuit-breaker state transitions.

## Known Limitations / Future Work

- **Not yet OpenAI-compatible** — uses a custom `/chat` schema rather than `/v1/chat/completions`
- **Router is LLM-based, not config-driven** — adds one classification call per cache miss (mitigated by checking cache before routing)
- **Rate limiter uses Redis `INCR`/`EXPIRE`**, not an atomic Lua script — a small race condition is possible under heavy concurrency
- **Semantic cache is in-memory, per-instance** — would need to move to a shared store (e.g., a vector DB or Redis) to support true horizontal scaling across multiple app instances
- **Single Dockerfile stage** — a multi-stage build would produce a smaller production image
- **No streaming (SSE) support** yet
- **No persistent storage for Grafana** — dashboards/data sources reset if the container is removed
- **Single hardcoded API key** — a real multi-tenant system would issue unique keys per customer with individual rate limits and usage tracking


