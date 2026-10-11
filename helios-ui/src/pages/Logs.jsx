import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Download, Search, Trash2 } from 'lucide-react';
import { clearLogs, getLogs } from '../api.js';
import { Drawer, StatusCode, useToast } from '../components/ui.jsx';

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'ok', label: 'Success' },
  { id: 'cached', label: 'Cache hits' },
  { id: 'errors', label: 'Errors' },
];
const PAGE_SIZE = 12;

export default function Logs() {
  const toast = useToast();
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState(null);

  const refresh = () => getLogs().then(setLogs);
  useEffect(() => {
    refresh();
  }, []);
  useEffect(() => setPage(0), [filter, query]);

  const filtered = logs.filter((l) => {
    if (filter === 'ok' && l.status !== 200) return false;
    if (filter === 'cached' && !l.cached) return false;
    if (filter === 'errors' && l.status === 200) return false;
    const q = query.toLowerCase();
    return !q || l.prompt.toLowerCase().includes(q) || l.keyName.toLowerCase().includes(q) || l.provider.toLowerCase().includes(q);
  });
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const rows = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  async function handleClear() {
    if (!confirm('Delete all request logs?')) return;
    await clearLogs();
    toast('Logs cleared');
    refresh();
  }

  function exportCsv() {
    const head = 'time,key,prompt,provider,status,cached,tokens,latency_ms,cost\n';
    const body = filtered
      .map((l) => [new Date(l.ts).toISOString(), l.keyName, `"${l.prompt.replace(/"/g, '""')}"`, l.provider, l.status, l.cached, l.tokens, l.latencyMs, l.cost].join(','))
      .join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([head + body], { type: 'text/csv' }));
    a.download = 'helios-logs.csv';
    a.click();
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Request Logs</h2>
          <p className="muted">Every request recorded by stage 8 of the pipeline. Click a row for details.</p>
        </div>
        <div className="head-actions">
          <button className="ghost" onClick={exportCsv}><Download size={15} /> Export CSV</button>
          <button className="ghost danger-text" onClick={handleClear}><Trash2 size={15} /> Clear</button>
        </div>
      </div>

      <div className="toolbar">
        <div className="segmented">
          {FILTERS.map((f) => (
            <button key={f.id} className={filter === f.id ? 'active' : ''} onClick={() => setFilter(f.id)}>{f.label}</button>
          ))}
        </div>
        <div className="search">
          <Search size={16} />
          <input placeholder="Search prompt, key or provider…" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
      </div>

      <div className="card flush">
        {rows.length === 0 ? (
          <p className="muted empty-row">No logs to show.</p>
        ) : (
          <table className="clickable">
            <thead>
              <tr>
                <th>Time</th><th>Key</th><th>Prompt</th><th>Provider</th><th>Status</th>
                <th className="num">Tokens</th><th className="num">Latency</th><th className="num">Cost</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((l) => (
                <tr key={l.id} onClick={() => setSelected(l)}>
                  <td className="muted">{new Date(l.ts).toLocaleTimeString()}</td>
                  <td>{l.keyName}</td>
                  <td className="truncate">{l.prompt}</td>
                  <td>{l.cached ? <span className="chip cache">Cache</span> : l.provider}</td>
                  <td><StatusCode code={l.status} /></td>
                  <td className="num">{l.tokens}</td>
                  <td className="num">{l.latencyMs} ms</td>
                  <td className="num">${l.cost}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="pager">
          <span className="muted">{filtered.length} results</span>
          <div>
            <button className="icon-btn" disabled={page === 0} onClick={() => setPage(page - 1)} aria-label="Previous"><ChevronLeft size={16} /></button>
            <span>Page {page + 1} of {pages}</span>
            <button className="icon-btn" disabled={page >= pages - 1} onClick={() => setPage(page + 1)} aria-label="Next"><ChevronRight size={16} /></button>
          </div>
        </div>
      </div>

      {selected && (
        <Drawer title={`Request #${selected.id}`} onClose={() => setSelected(null)}>
          <dl className="details">
            <dt>Status</dt><dd><StatusCode code={selected.status} /></dd>
            <dt>Time</dt><dd>{new Date(selected.ts).toLocaleString()}</dd>
            <dt>API key</dt><dd>{selected.keyName}</dd>
            <dt>Provider</dt><dd>{selected.provider}</dd>
            <dt>Model</dt><dd><code>{selected.model}</code></dd>
            <dt>Cache</dt><dd>{selected.cached ? 'Hit' : 'Miss'}</dd>
            <dt>Tokens</dt><dd>{selected.tokens}</dd>
            <dt>Latency</dt><dd>{selected.latencyMs} ms</dd>
            <dt>Cost</dt><dd>${selected.cost}</dd>
          </dl>
          <h4>Prompt</h4>
          <pre className="code">{selected.prompt}</pre>
          {selected.reply && (<><h4>Response</h4><pre className="code">{selected.reply}</pre></>)}
        </Drawer>
      )}
    </div>
  );
}
