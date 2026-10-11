// All data access for the UI lives here.
// Right now it uses mock data stored in localStorage.
// When your backend is ready, set USE_MOCK = false and point BASE_URL at it;
// every function below then calls the matching REST endpoint instead.

const USE_MOCK = false;
const BASE_URL = 'http://localhost:8000/api';
const STORAGE_KEY = 'helios-db-v2';

async function http(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.status === 204 ? null : res.json();
}

// ---------- mock storage ----------
const PROVIDERS = [
  { id: 1, name: 'OpenAI', model: 'gpt-4o-mini', priority: 1, enabled: true, status: 'healthy', costPer1k: 0.15, region: 'us-east' },
  { id: 2, name: 'Groq', model: 'llama-3.1-8b-instant', priority: 2, enabled: true, status: 'healthy', costPer1k: 0.05, region: 'us-west' },
  { id: 3, name: 'Gemini', model: 'gemini-1.5-flash', priority: 3, enabled: true, status: 'degraded', costPer1k: 0.075, region: 'eu-west' },
  { id: 4, name: 'Ollama', model: 'llama3:8b (local)', priority: 4, enabled: false, status: 'down', costPer1k: 0, region: 'local' },
];

const KEYS = [
  { id: 1, name: 'Demo Chat App', key: 'hk_live_8f2a91c4d7', rateLimit: 60, monthlyBudget: 5, spent: 0, active: true, createdAt: '2026-09-01' },
  { id: 2, name: 'Test Script', key: 'hk_test_3c7d10e2b9', rateLimit: 20, monthlyBudget: 1, spent: 0, active: true, createdAt: '2026-09-15' },
  { id: 3, name: 'Load Tester', key: 'hk_load_a19be04f63', rateLimit: 500, monthlyBudget: 10, spent: 0, active: true, createdAt: '2026-09-20' },
  { id: 4, name: 'Old Prototype', key: 'hk_old_77d3a5f1c0', rateLimit: 30, monthlyBudget: 2, spent: 0, active: false, createdAt: '2026-08-10' },
];

const SAMPLE_PROMPTS = [
  'Summarize this article in 3 bullet points',
  'What is a circuit breaker pattern?',
  'Translate "good morning" to French',
  'Explain Redis in one paragraph',
  'Write a haiku about distributed systems',
  'What is the capital of Japan?',
  'Give me 5 names for a coffee shop',
  'How does rate limiting work?',
];

// Builds 24 hours of realistic-looking history so the dashboard isn't empty.
function buildSeed() {
  const db = { providers: structuredClone(PROVIDERS), apiKeys: structuredClone(KEYS), logs: [] };
  const now = Date.now();
  let id = 1;
  let rand = 42;
  const rnd = () => ((rand = (rand * 16807) % 2147483647) / 2147483647);

  for (let h = 23; h >= 0; h--) {
    const perHour = 6 + Math.round(10 * Math.sin(((24 - h) / 24) * Math.PI) + rnd() * 6);
    for (let i = 0; i < perHour; i++) {
      const ts = now - h * 3_600_000 - Math.floor(rnd() * 3_600_000);
      const key = db.apiKeys[Math.floor(rnd() * 3)];
      const prompt = SAMPLE_PROMPTS[Math.floor(rnd() * SAMPLE_PROMPTS.length)];
      const roll = rnd();
      const provider = db.providers[roll < 0.55 ? 0 : roll < 0.85 ? 1 : 2];
      const status = roll > 0.97 ? 429 : roll > 0.95 ? 503 : 200;
      const cached = status === 200 && rnd() < 0.35;
      const tokens = status === 200 ? 80 + Math.floor(rnd() * 600) : 0;
      const cost = status === 200 && !cached ? +((tokens / 1000) * provider.costPer1k).toFixed(5) : 0;
      if (status === 200) key.spent = +(key.spent + cost).toFixed(5);
      db.logs.push({
        id: id++,
        ts,
        keyName: key.name,
        prompt,
        provider: status === 200 ? provider.name : '-',
        model: status === 200 ? provider.model : '-',
        status,
        cached,
        tokens,
        latencyMs: cached ? 3 + Math.floor(rnd() * 8) : status === 200 ? 250 + Math.floor(rnd() * 900) : 2,
        cost,
        reply: status === 200 ? `[sample reply from ${provider.name}]` : '',
      });
    }
  }
  db.logs.sort((a, b) => a.ts - b.ts);
  db.logs.forEach((l, i) => (l.id = i + 1));
  return db;
}

function load() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) return JSON.parse(raw);
  const db = buildSeed();
  save(db);
  return db;
}
function save(db) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
}
const nextId = (rows) => (rows.length ? Math.max(...rows.map((r) => r.id)) + 1 : 1);
const delay = (v, ms = 150) => new Promise((r) => setTimeout(() => r(v), ms));

export function resetDemoData() {
  localStorage.removeItem(STORAGE_KEY);
  load();
}

// ---------- providers ----------
export async function getProviders() {
  if (!USE_MOCK) return http('/providers');
  const { providers, logs } = load();
  const withStats = providers.map((p) => {
    const mine = logs.filter((l) => l.provider === p.name);
    const live = mine.filter((l) => !l.cached);
    return {
      ...p,
      requests: mine.length,
      avgLatency: live.length ? Math.round(live.reduce((s, l) => s + l.latencyMs, 0) / live.length) : 0,
      cost: +mine.reduce((s, l) => s + l.cost, 0).toFixed(4),
    };
  });
  return delay(withStats.sort((a, b) => a.priority - b.priority));
}

export async function updateProvider(id, changes) {
  if (!USE_MOCK) return http(`/providers/${id}`, { method: 'PUT', body: changes });
  const db = load();
  db.providers = db.providers.map((p) => (p.id === id ? { ...p, ...changes } : p));
  save(db);
  return delay(db.providers.find((p) => p.id === id), 50);
}

// Swap priority with the neighbour above (-1) or below (+1).
export async function moveProvider(id, direction) {
  if (!USE_MOCK) return http(`/providers/${id}/move`, { method: 'POST', body: { direction } });
  const db = load();
  const sorted = [...db.providers].sort((a, b) => a.priority - b.priority);
  const i = sorted.findIndex((p) => p.id === id);
  const j = i + direction;
  if (j < 0 || j >= sorted.length) return delay(null, 0);
  [sorted[i].priority, sorted[j].priority] = [sorted[j].priority, sorted[i].priority];
  save(db);
  return delay(null, 50);
}

// ---------- api keys ----------
export async function getApiKeys() {
  if (!USE_MOCK) return http('/keys');
  const { apiKeys, logs } = load();
  return delay(apiKeys.map((k) => ({ ...k, requests: logs.filter((l) => l.keyName === k.name).length })));
}

export async function createApiKey({ name, rateLimit, monthlyBudget }) {
  const body = { name, rateLimit: Number(rateLimit), monthlyBudget: Number(monthlyBudget) };
  if (!USE_MOCK) return http('/keys', { method: 'POST', body });
  const db = load();
  const row = {
    id: nextId(db.apiKeys),
    ...body,
    key: 'hk_live_' + Math.random().toString(16).slice(2, 12),
    spent: 0,
    active: true,
    createdAt: new Date().toISOString().slice(0, 10),
  };
  db.apiKeys.push(row);
  save(db);
  return delay(row);
}

export async function toggleApiKey(id, active) {
  if (!USE_MOCK) return http(`/keys/${id}`, { method: 'PUT', body: { active } });
  const db = load();
  db.apiKeys = db.apiKeys.map((k) => (k.id === id ? { ...k, active } : k));
  save(db);
  return delay(null);
}

export async function deleteApiKey(id) {
  if (!USE_MOCK) return http(`/keys/${id}`, { method: 'DELETE' });
  const db = load();
  db.apiKeys = db.apiKeys.filter((k) => k.id !== id);
  save(db);
  return delay(null);
}

// ---------- request logs ----------
export async function getLogs() {
  if (!USE_MOCK) return http('/logs');
  return delay([...load().logs].reverse());
}

export async function clearLogs() {
  if (!USE_MOCK) return http('/logs', { method: 'DELETE' });
  const db = load();
  db.logs = [];
  save(db);
  return delay(null);
}

// ---------- dashboard stats ----------
export async function getStats() {
  if (!USE_MOCK) return http('/stats');
  const { logs, apiKeys, providers } = load();
  const total = logs.length;
  const live = logs.filter((l) => l.status === 200 && !l.cached);

  // last 24 hourly buckets
  const now = Date.now();
  const hourly = Array.from({ length: 24 }, (_, i) => {
    const start = now - (24 - i) * 3_600_000;
    const end = start + 3_600_000;
    const inHour = logs.filter((l) => l.ts >= start && l.ts < end);
    const liveHour = inHour.filter((l) => l.status === 200 && !l.cached);
    return {
      label: new Date(end).toLocaleTimeString([], { hour: 'numeric' }),
      cached: inHour.filter((l) => l.cached).length,
      live: inHour.filter((l) => !l.cached).length,
      latency: liveHour.length ? Math.round(liveHour.reduce((s, l) => s + l.latencyMs, 0) / liveHour.length) : null,
    };
  });

  return delay({
    totalRequests: total,
    cacheHitRate: total ? Math.round((logs.filter((l) => l.cached).length / total) * 100) : 0,
    errorRate: total ? +((logs.filter((l) => l.status !== 200).length / total) * 100).toFixed(1) : 0,
    avgLatency: live.length ? Math.round(live.reduce((s, l) => s + l.latencyMs, 0) / live.length) : 0,
    totalCost: logs.reduce((s, l) => s + l.cost, 0).toFixed(4),
    moneySaved: logs.filter((l) => l.cached).reduce((s, l) => s + (l.tokens / 1000) * 0.15, 0).toFixed(4),
    activeKeys: apiKeys.filter((k) => k.active).length,
    totalKeys: apiKeys.length,
    healthyProviders: providers.filter((p) => p.enabled && p.status === 'healthy').length,
    totalProviders: providers.length,
    hourly,
    byProvider: providers.map((p) => ({ name: p.name, value: logs.filter((l) => l.provider === p.name).length })),
    recent: [...logs].reverse().slice(0, 6),
    providers,
  });
}

// ---------- playground (simulates the 8-stage pipeline) ----------
export const PIPELINE_STAGES = [
  { id: 'auth', label: 'Auth', hint: 'valid API key?' },
  { id: 'rate', label: 'Rate Limit', hint: 'under limit & budget?' },
  { id: 'cache', label: 'Cache Check', hint: 'seen this before?' },
  { id: 'router', label: 'Router', hint: 'pick best provider' },
  { id: 'breaker', label: 'Circuit Breaker', hint: 'provider healthy?' },
  { id: 'llm', label: 'Call LLM', hint: 'get the answer' },
  { id: 'save', label: 'Save to Cache', hint: 'store for next time' },
  { id: 'log', label: 'Log + Metrics', hint: 'record cost & latency' },
];

// Returns { status, reply, provider, ..., trace: [{ stage, result: pass|fail|hit|skip, detail }] }
export async function sendChat({ apiKey, prompt }) {
  if (!USE_MOCK) return http('/chat', { method: 'POST', body: { apiKey, prompt } });

  const db = load();
  const trace = [];
  const step = (stage, result, detail) => trace.push({ stage, result, detail });
  const key = db.apiKeys.find((k) => k.key === apiKey);
  const log = { id: nextId(db.logs), ts: Date.now(), keyName: key?.name ?? 'unknown', prompt, provider: '-', model: '-', cached: false, tokens: 0, cost: 0 };

  const finish = (fields) => {
    Object.assign(log, fields);
    const done = new Set(trace.map((t) => t.stage));
    PIPELINE_STAGES.forEach((s) => !done.has(s.id) && s.id !== 'log' && step(s.id, 'skip', 'skipped'));
    step('log', 'pass', `logged as #${log.id}`);
    trace.sort((a, b) => PIPELINE_STAGES.findIndex((s) => s.id === a.stage) - PIPELINE_STAGES.findIndex((s) => s.id === b.stage));
    db.logs.push(log);
    save(db);
    return delay({ ...log, trace }, 400);
  };

  // 1. auth
  if (!key || !key.active) {
    step('auth', 'fail', key ? 'key is revoked' : 'unknown key');
    return finish({ status: 401, latencyMs: 2, reply: '401 Unauthorized — invalid or revoked API key.' });
  }
  step('auth', 'pass', key.name);

  // 2. rate limit + budget
  const recent = db.logs.filter((l) => l.keyName === key.name && l.ts > Date.now() - 60_000).length;
  if (recent >= key.rateLimit) {
    step('rate', 'fail', `${recent}/${key.rateLimit} req/min`);
    return finish({ status: 429, latencyMs: 2, reply: '429 Too Many Requests — rate limit exceeded, retry in a minute.' });
  }
  if (key.spent >= key.monthlyBudget) {
    step('rate', 'fail', `budget $${key.monthlyBudget} used up`);
    return finish({ status: 402, latencyMs: 3, reply: '402 Payment Required — monthly budget exceeded.' });
  }
  step('rate', 'pass', `${recent + 1}/${key.rateLimit} req/min`);

  // 3. cache
  const hit = [...db.logs].reverse().find((l) => l.prompt.toLowerCase() === prompt.toLowerCase() && l.status === 200 && l.reply && !l.reply.startsWith('[sample'));
  if (hit) {
    step('cache', 'hit', 'HIT — no LLM call, $0');
    return finish({ status: 200, cached: true, provider: hit.provider, model: hit.model, tokens: hit.tokens, latencyMs: 4, reply: hit.reply });
  }
  step('cache', 'pass', 'miss');

  // 4. router + 5. circuit breaker (failover)
  const candidates = db.providers.filter((p) => p.enabled).sort((a, b) => a.priority - b.priority);
  step('router', candidates.length ? 'pass' : 'fail', candidates.length ? `order: ${candidates.map((p) => p.name).join(' → ')}` : 'no providers enabled');
  const chosen = candidates.find((p) => p.status !== 'down');
  const skipped = candidates.slice(0, candidates.indexOf(chosen)).map((p) => p.name);
  if (!chosen) {
    step('breaker', 'fail', 'all providers open');
    return finish({ status: 503, latencyMs: 5, reply: '503 Service Unavailable — every provider is down.' });
  }
  step('breaker', 'pass', skipped.length ? `failover: skipped ${skipped.join(', ')}` : `${chosen.name} closed (healthy)`);

  // 6. call llm
  const tokens = 40 + prompt.length * 3;
  const latencyMs = (chosen.status === 'degraded' ? 900 : 250) + Math.floor(Math.random() * 500);
  step('llm', 'pass', `${chosen.name} · ${latencyMs} ms`);
  step('save', 'pass', 'stored in cache');
  const cost = +((tokens / 1000) * chosen.costPer1k).toFixed(5);
  key.spent = +(key.spent + cost).toFixed(5);

  return finish({
    status: 200,
    provider: chosen.name,
    model: chosen.model,
    tokens,
    latencyMs,
    cost,
    failover: skipped,
    reply: `This is a simulated answer from ${chosen.name} (${chosen.model}).\n\nYou asked: "${prompt}"\n\nOnce the backend is connected, the real model response appears here.`,
  });
}
