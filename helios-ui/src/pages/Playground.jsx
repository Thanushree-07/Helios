import { useEffect, useRef, useState } from 'react';
import { Check, Copy, Loader2, Send, SkipForward, X, Zap } from 'lucide-react';
import { getApiKeys, PIPELINE_STAGES, sendChat } from '../api.js';
import { StatusCode, useToast } from '../components/ui.jsx';

const EXAMPLES = ['What is a circuit breaker pattern?', 'Explain Redis in one paragraph', 'Write a haiku about distributed systems'];

const ICONS = { pass: Check, fail: X, hit: Zap, skip: SkipForward };

export default function Playground() {
  const toast = useToast();
  const [keys, setKeys] = useState([]);
  const [apiKey, setApiKey] = useState('');
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [trace, setTrace] = useState([]);
  const [shown, setShown] = useState(0);
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    getApiKeys().then((k) => {
      setKeys(k);
      const first = k.find((x) => x.active);
      if (first) setApiKey(first.key);
    });
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  // reveal pipeline stages one by one
  useEffect(() => {
    if (shown >= trace.length) return;
    const t = setTimeout(() => setShown((s) => s + 1), 180);
    return () => clearTimeout(t);
  }, [shown, trace]);

  async function send(text) {
    const q = (text ?? prompt).trim();
    if (!q || loading) return;
    setPrompt('');
    setLoading(true);
    setTrace([]);
    setShown(0);
    setMessages((m) => [...m, { role: 'user', text: q }]);
    const res = await sendChat({ apiKey, prompt: q });
    setTrace(res.trace || []);
    setMessages((m) => [...m, { role: 'bot', ...res }]);
    setLoading(false);
    if (res.status !== 200) toast(`Request blocked: ${res.status}`, 'error');
  }

  const curl = `curl http://localhost:8000/v1/chat/completions \\
  -H "Authorization: Bearer ${apiKey || 'hk_...'}" \\
  -d '{"model":"auto","messages":[{"role":"user","content":"Hello"}]}'`;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Playground</h2>
          <p className="muted">Send a prompt and watch it travel through the 8-stage pipeline.</p>
        </div>
        <select value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="key-select">
          {keys.map((k) => (
            <option key={k.id} value={k.key}>{k.name}{k.active ? '' : ' (revoked)'}</option>
          ))}
          <option value="hk_invalid">Invalid key (test 401)</option>
        </select>
      </div>

      <div className="playground">
        <section className="card chat">
          <div className="messages">
            {messages.length === 0 && (
              <div className="empty">
                <Zap size={28} />
                <p>Try one of these, then send it again to see a cache hit:</p>
                <div className="examples">
                  {EXAMPLES.map((e) => <button key={e} className="ghost" onClick={() => send(e)}>{e}</button>)}
                </div>
              </div>
            )}
            {messages.map((m, i) =>
              m.role === 'user' ? (
                <div key={i} className="msg user">{m.text}</div>
              ) : (
                <div key={i} className="msg bot">
                  <div className="msg-meta">
                    <StatusCode code={m.status} />
                    {m.cached && <span className="chip cache"><Zap size={12} /> Cache hit</span>}
                    {m.failover?.length > 0 && <span className="chip degraded">Failover</span>}
                    <span className="muted">{m.provider !== '-' && `${m.provider} · `}{m.latencyMs} ms · ${m.cost}</span>
                  </div>
                  <p>{m.reply}</p>
                </div>
              )
            )}
            {loading && <div className="msg bot typing"><Loader2 size={16} className="spin" /> Routing request…</div>}
            <div ref={endRef} />
          </div>
          <form className="composer" onSubmit={(e) => { e.preventDefault(); send(); }}>
            <input value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Ask anything…" />
            <button className="btn" disabled={loading || !prompt.trim()}><Send size={16} /> Send</button>
          </form>
        </section>

        <aside className="side">
          <section className="card">
            <h3>Request pipeline</h3>
            <ol className="pipeline">
              {PIPELINE_STAGES.map((s, i) => {
                const t = trace.find((x) => x.stage === s.id);
                const visible = t && trace.indexOf(t) < shown;
                const state = visible ? t.result : loading ? 'wait' : 'idle';
                const Icon = ICONS[state];
                return (
                  <li key={s.id} className={`stage ${state}`}>
                    <span className="stage-dot">{Icon ? <Icon size={13} /> : i + 1}</span>
                    <div>
                      <b>{s.label}</b>
                      <span>{visible ? t.detail : s.hint}</span>
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>

          <section className="card">
            <div className="card-head">
              <h3>Use it from code</h3>
              <button className="icon-btn" onClick={() => { navigator.clipboard.writeText(curl); toast('Copied to clipboard'); }} aria-label="Copy"><Copy size={16} /></button>
            </div>
            <pre className="code">{curl}</pre>
          </section>
        </aside>
      </div>
    </div>
  );
}
