import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, ArrowRight, Clock, Database, DollarSign, KeyRound, PiggyBank, Server } from 'lucide-react';
import { getStats } from '../api.js';
import { HBars, LineChart, Legend, StackedBars } from '../components/Charts.jsx';
import { Health, StatusCode, timeAgo } from '../components/ui.jsx';

const SERIES = [
  { key: 'live', label: 'LLM calls', color: 'var(--series-1)' },
  { key: 'cached', label: 'Cache hits', color: 'var(--series-2)' },
];

export default function Dashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getStats().then(setStats);
  }, []);

  if (!stats) return <div className="skeleton-grid">{Array.from({ length: 4 }, (_, i) => <div key={i} className="skeleton" />)}</div>;

  const kpis = [
    { label: 'Requests (24h)', value: stats.totalRequests.toLocaleString(), icon: Activity, sub: 'through the gateway' },
    { label: 'Cache hit rate', value: `${stats.cacheHitRate}%`, icon: Database, sub: 'served without an LLM call' },
    { label: 'Avg latency', value: `${stats.avgLatency} ms`, icon: Clock, sub: 'live LLM calls only' },
    { label: 'Error rate', value: `${stats.errorRate}%`, icon: AlertTriangle, sub: '4xx + 5xx responses' },
    { label: 'Total spend', value: `$${stats.totalCost}`, icon: DollarSign, sub: 'across all providers' },
    { label: 'Saved by cache', value: `$${stats.moneySaved}`, icon: PiggyBank, sub: 'estimated' },
    { label: 'Active keys', value: `${stats.activeKeys}/${stats.totalKeys}`, icon: KeyRound, sub: 'client apps' },
    { label: 'Healthy providers', value: `${stats.healthyProviders}/${stats.totalProviders}`, icon: Server, sub: 'circuit closed' },
  ];

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Overview</h2>
          <p className="muted">Traffic, cost and health of your gateway over the last 24 hours.</p>
        </div>
        <Link to="/playground" className="btn">Send a test request <ArrowRight size={16} /></Link>
      </div>

      <div className="kpis">
        {kpis.map(({ label, value, icon: Icon, sub }) => (
          <div className="kpi" key={label}>
            <div className="kpi-icon"><Icon size={18} /></div>
            <span className="kpi-label">{label}</span>
            <strong>{value}</strong>
            <span className="kpi-sub">{sub}</span>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <section className="card span-2">
          <div className="card-head">
            <div>
              <h3>Requests per hour</h3>
              <p className="muted">LLM calls vs. answers served from cache</p>
            </div>
            <Legend series={SERIES} />
          </div>
          <StackedBars data={stats.hourly} series={SERIES} />
        </section>

        <section className="card">
          <div className="card-head">
            <div>
              <h3>Average latency</h3>
              <p className="muted">Live LLM calls, ms per hour</p>
            </div>
          </div>
          <LineChart data={stats.hourly} dataKey="latency" color="var(--series-1)" unit=" ms" />
        </section>

        <section className="card">
          <div className="card-head">
            <div>
              <h3>Traffic by provider</h3>
              <p className="muted">Requests routed in 24h</p>
            </div>
          </div>
          <HBars data={stats.byProvider} color="var(--series-1)" />
          <div className="provider-health">
            {stats.providers.map((p) => (
              <div key={p.id} className="ph-row">
                <span>{p.name}</span>
                {p.enabled ? <Health status={p.status} /> : <span className="chip off">Disabled</span>}
              </div>
            ))}
          </div>
        </section>

        <section className="card span-2">
          <div className="card-head">
            <h3>Recent requests</h3>
            <Link to="/logs" className="link">View all <ArrowRight size={14} /></Link>
          </div>
          <table>
            <thead>
              <tr><th>When</th><th>Key</th><th>Prompt</th><th>Provider</th><th>Status</th><th className="num">Latency</th></tr>
            </thead>
            <tbody>
              {stats.recent.map((l) => (
                <tr key={l.id}>
                  <td className="muted">{timeAgo(l.ts)}</td>
                  <td>{l.keyName}</td>
                  <td className="truncate">{l.prompt}</td>
                  <td>{l.cached ? <span className="chip cache">Cache</span> : l.provider}</td>
                  <td><StatusCode code={l.status} /></td>
                  <td className="num">{l.latencyMs} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
