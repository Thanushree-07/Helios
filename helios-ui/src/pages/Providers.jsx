import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, Cpu, Globe } from 'lucide-react';
import { getProviders, moveProvider, updateProvider } from '../api.js';
import { Health, Switch, useToast } from '../components/ui.jsx';

const STATUSES = ['healthy', 'degraded', 'down'];

export default function Providers() {
  const toast = useToast();
  const [providers, setProviders] = useState([]);

  const refresh = () => getProviders().then(setProviders);
  useEffect(() => {
    refresh();
  }, []);

  async function change(p, changes, message) {
    await updateProvider(p.id, changes);
    toast(message);
    refresh();
  }

  async function move(p, dir) {
    await moveProvider(p.id, dir);
    refresh();
  }

  const route = providers.filter((p) => p.enabled && p.status !== 'down');

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Providers</h2>
          <p className="muted">Requests go to the highest-priority healthy provider. If its circuit opens, Helios fails over to the next.</p>
        </div>
      </div>

      <div className="card route">
        <span className="muted">Current routing order</span>
        <div className="route-chain">
          {route.length === 0 && <span className="chip down">No provider available — requests return 503</span>}
          {route.map((p, i) => (
            <span key={p.id} className="route-step">
              {i > 0 && <span className="arrow">→</span>}
              <span className={`route-node ${i === 0 ? 'primary' : ''}`}>{p.name}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="provider-list">
        {providers.map((p, i) => (
          <div key={p.id} className={`card provider ${p.enabled ? '' : 'inactive'}`}>
            <div className="prio">
              <button className="icon-btn" disabled={i === 0} onClick={() => move(p, -1)} aria-label="Move up"><ChevronUp size={16} /></button>
              <b>#{p.priority}</b>
              <button className="icon-btn" disabled={i === providers.length - 1} onClick={() => move(p, 1)} aria-label="Move down"><ChevronDown size={16} /></button>
            </div>

            <div className="provider-main">
              <div className="provider-title">
                <h3>{p.name}</h3>
                {p.enabled ? <Health status={p.status} /> : <span className="chip off">Disabled</span>}
              </div>
              <div className="provider-meta muted">
                <span><Cpu size={14} /> {p.model}</span>
                <span><Globe size={14} /> {p.region}</span>
                <span>${p.costPer1k}/1k tokens</span>
              </div>
            </div>

            <div className="provider-stats">
              <div><span className="muted">Requests</span><b>{p.requests}</b></div>
              <div><span className="muted">Avg latency</span><b>{p.avgLatency} ms</b></div>
              <div><span className="muted">Spend</span><b>${p.cost}</b></div>
            </div>

            <div className="provider-controls">
              <label className="muted">
                Simulate
                <select value={p.status} onChange={(e) => change(p, { status: e.target.value }, `${p.name} marked ${e.target.value}`)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
              <Switch checked={p.enabled} onChange={(v) => change(p, { enabled: v }, `${p.name} ${v ? 'enabled' : 'disabled'}`)} label={`Toggle ${p.name}`} />
            </div>
          </div>
        ))}
      </div>
      <p className="muted hint">Tip: set OpenAI to “down”, then send a prompt in the Playground to watch the failover.</p>
    </div>
  );
}
