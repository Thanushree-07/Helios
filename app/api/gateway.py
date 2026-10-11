import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models import APIKey, Provider, RequestLog
from app.schemas.chat import ChatRequest
import datetime
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import Provider, APIKey, RequestLog
from app.schemas.gateway import ProviderOut, ProviderUpdate, APIKeyCreate, APIKeyOut

router = APIRouter(prefix="/api")


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(db: Session = Depends(get_db)):
    return db.query(Provider).order_by(Provider.priority).all()


@router.put("/providers/{provider_id}", response_model=ProviderOut)
def update_provider(provider_id: int, changes: ProviderUpdate, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if changes.enabled is not None:
        provider.enabled = changes.enabled
    if changes.status is not None:
        provider.status = changes.status
    db.commit()
    db.refresh(provider)
    return provider


@router.post("/providers/{provider_id}/move")
def move_provider(provider_id: int, direction: dict, db: Session = Depends(get_db)):
    providers = db.query(Provider).order_by(Provider.priority).all()
    idx = next(i for i, p in enumerate(providers) if p.id == provider_id)
    j = idx + direction.get("direction", 0)
    if 0 <= j < len(providers):
        providers[idx].priority, providers[j].priority = providers[j].priority, providers[idx].priority
        db.commit()
    return {"ok": True}


@router.get("/keys", response_model=list[APIKeyOut])
def list_keys(db: Session = Depends(get_db)):
    keys = db.query(APIKey).all()
    return [
        APIKeyOut(
            id=k.id, name=k.name, key=k.key, rate_limit=k.rate_limit,
            monthly_budget=k.monthly_budget, spent=k.spent, active=k.active,
            created_at=str(k.created_at.date()) if k.created_at else "",
        )
        for k in keys
    ]


@router.post("/keys", response_model=APIKeyOut)
def create_key(body: APIKeyCreate, db: Session = Depends(get_db)):
    import secrets
    new_key = APIKey(
        name=body.name,
        key="hk_live_" + secrets.token_hex(6),
        rate_limit=body.rate_limit,
        monthly_budget=body.monthly_budget,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    return APIKeyOut(
        id=new_key.id, name=new_key.name, key=new_key.key, rate_limit=new_key.rate_limit,
        monthly_budget=new_key.monthly_budget, spent=new_key.spent, active=new_key.active,
        created_at=str(new_key.created_at.date()) if new_key.created_at else "",
    )


@router.put("/keys/{key_id}")
def toggle_key(key_id: int, body: dict, db: Session = Depends(get_db)):
    k = db.query(APIKey).filter(APIKey.id == key_id).first()
    k.active = body.get("active", k.active)
    db.commit()
    return {"ok": True}


@router.delete("/keys/{key_id}")
def delete_key(key_id: int, db: Session = Depends(get_db)):
    db.query(APIKey).filter(APIKey.id == key_id).delete()
    db.commit()
    return {"ok": True}


@router.get("/logs")
def list_logs(db: Session = Depends(get_db)):
    logs = db.query(RequestLog).order_by(RequestLog.ts.desc()).all()
    return [
        {
            "id": l.id, "ts": l.ts, "keyName": l.key_name, "prompt": l.prompt,
            "provider": l.provider, "model": l.model, "status": l.status,
            "cached": l.cached, "tokens": l.tokens, "latencyMs": l.latency_ms,
            "cost": l.cost, "reply": l.reply,
        }
        for l in logs
    ]


@router.delete("/logs")
def clear_logs(db: Session = Depends(get_db)):
    db.query(RequestLog).delete()
    db.commit()
    return {"ok": True}

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _hourly_buckets(db):
    """Last 24 one-hour buckets built from the real request logs."""
    HOUR = 3_600_000
    now_ms = int(time.time() * 1000)
    logs = db.query(RequestLog).filter(RequestLog.ts >= now_ms - 24 * HOUR).all()

    buckets = []
    for i in range(24):
        start = now_ms - (24 - i) * HOUR
        end = start + HOUR
        in_hour = [l for l in logs if start < l.ts <= end]
        cached = sum(1 for l in in_hour if l.cached)
        live_ok = [l for l in in_hour if l.status == 200 and not l.cached]
        label = datetime.datetime.fromtimestamp(end / 1000, IST).strftime("%I %p").lstrip("0")
        buckets.append({
            "label": label,
            "cached": cached,
            "live": len(in_hour) - cached,
            "latency": round(sum(l.latency_ms for l in live_ok) / len(live_ok)) if live_ok else None,
        })
    return buckets
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    logs = db.query(RequestLog).all()
    keys = db.query(APIKey).all()
    providers = db.query(Provider).all()

    total = len(logs)
    cached_count = sum(1 for l in logs if l.cached)
    error_count = sum(1 for l in logs if l.status != 200)
    live_latencies = [l.latency_ms for l in logs if l.status == 200 and not l.cached]

    return {
        "totalRequests": total,
        "cacheHitRate": round((cached_count / total) * 100) if total else 0,
        "errorRate": round((error_count / total) * 100, 1) if total else 0,
        "avgLatency": round(sum(live_latencies) / len(live_latencies)) if live_latencies else 0,
        "totalCost": round(sum(l.cost for l in logs), 4),
        "moneySaved": round(sum((l.tokens / 1000) * 0.15 for l in logs if l.cached), 4),
        "activeKeys": sum(1 for k in keys if k.active),
        "totalKeys": len(keys),
        "healthyProviders": sum(1 for p in providers if p.enabled and p.status == "healthy"),
        "totalProviders": len(providers),
        "hourly": _hourly_buckets(db),
        "byProvider": [{"name": p.name, "value": sum(1 for l in logs if (l.provider or "").lower() == p.name.lower())} for p in providers],
        "recent": [
            {
                "id": l.id, "ts": l.ts, "keyName": l.key_name, "prompt": l.prompt,
                "provider": l.provider, "model": l.model, "status": l.status,
                "cached": l.cached, "tokens": l.tokens, "latencyMs": l.latency_ms,
                "cost": l.cost, "reply": l.reply,
            }
            for l in sorted(logs, key=lambda x: x.ts, reverse=True)[:6]
        ],
        "providers": [
            {
                "id": p.id, "name": p.name, "model": p.model, "priority": p.priority,
                "enabled": p.enabled, "status": p.status, "costPer1k": p.cost_per_1k, "region": p.region,
            }
            for p in providers
        ],
    }
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService

chat_service = ChatService()


@router.post("/chat")
def playground_chat(body: dict, db: Session = Depends(get_db)):
    api_key = body.get("apiKey")
    prompt = (body.get("prompt") or "").strip()

    def fail(status, reply, trace):
        return {"status": status, "reply": reply, "provider": "-", "model": "-",
                "tokens": 0, "latencyMs": 0, "cost": 0, "cached": False,
                "failover": [], "trace": trace}

    key_row = db.query(APIKey).filter(APIKey.key == api_key).first()
    if not key_row or not key_row.active:
        return fail(401, "401 Unauthorized — invalid or revoked API key.",
                    [{"stage": "auth", "result": "fail", "detail": "Invalid or revoked API key"}])
    if not prompt:
        return fail(400, "Prompt is empty.",
                    [{"stage": "auth", "result": "pass", "detail": f"Key '{key_row.name}' accepted"}])

    trace = [{"stage": "auth", "result": "pass", "detail": f"Key '{key_row.name}' accepted"}]

    start = time.perf_counter()
    try:
        out = chat_service.run(ChatRequest(prompt=prompt), client_id=api_key)
    except HTTPException as e:
        stage = "rate" if e.status_code == 429 else "llm"
        trace.append({"stage": stage, "result": "fail", "detail": str(e.detail)})
        return fail(e.status_code, str(e.detail), trace)
    except Exception as e:
        trace.append({"stage": "llm", "result": "fail", "detail": str(e)})
        return fail(500, str(e), trace)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    reply = out["response"]
    tokens = len(reply.split()) * 2  # rough estimate, not exact token count
    prow = db.query(Provider).filter(func.lower(Provider.name) == out["provider"].lower()).first()

    model = prow.model if prow else "-"
    cost = round(tokens / 1000 * prow.cost_per_1k, 5) if prow else 0.0
    cached = out["cache"] is not None

    log = RequestLog(
        ts=int(time.time() * 1000), key_name=key_row.name, prompt=prompt,
        provider=out["provider"], model=model, status=200, cached=cached,
        tokens=tokens, latency_ms=elapsed_ms, cost=cost, reply=reply,
    )
    db.add(log)
    db.commit()

    trace.append({"stage": "rate", "result": "pass", "detail": "Within rate limit"})
    trace.extend(out["trace"])
    trace.append({"stage": "log", "result": "pass", "detail": "Saved to PostgreSQL"})

    return {
        "status": 200, "reply": reply, "provider": out["provider"], "model": model,
        "tokens": tokens, "latencyMs": elapsed_ms, "cost": cost, "cached": cached,
        "failover": out["failover"], "trace": trace,
    }