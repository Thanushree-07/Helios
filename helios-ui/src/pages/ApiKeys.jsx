import { useEffect, useState } from 'react';
import { Copy, KeyRound, Plus, Search, Trash2 } from 'lucide-react';
import { createApiKey, deleteApiKey, getApiKeys, toggleApiKey } from '../api.js';
import { Modal, Progress, Switch, useToast } from '../components/ui.jsx';

const empty = { name: '', rateLimit: 60, monthlyBudget: 5 };

export default function ApiKeys() {
  const toast = useToast();
  const [keys, setKeys] = useState([]);
  const [form, setForm] = useState(empty);
  const [open, setOpen] = useState(false);
  const [created, setCreated] = useState(null);
  const [query, setQuery] = useState('');

  const refresh = () => getApiKeys().then(setKeys);
  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.name.trim()) return;
    const row = await createApiKey(form);
    setCreated(row);
    setForm(empty);
    refresh();
  }

  async function handleDelete(k) {
    if (!confirm(`Delete "${k.name}"? Apps using it will get 401 errors.`)) return;
    await deleteApiKey(k.id);
    toast('API key deleted');
    refresh();
  }

  async function handleToggle(k) {
    await toggleApiKey(k.id, !k.active);
    toast(k.active ? `${k.name} revoked` : `${k.name} activated`);
    refresh();
  }

  function copy(text) {
    navigator.clipboard.writeText(text);
    toast('Key copied to clipboard');
  }

  function close() {
    setOpen(false);
    setCreated(null);
  }

  const shown = keys.filter((k) => k.name.toLowerCase().includes(query.toLowerCase()));
  const mask = (key) => key.slice(0, 8) + '••••••' + key.slice(-3);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>API Keys</h2>
          <p className="muted">Each client app gets its own key with a rate limit and monthly budget.</p>
        </div>
        <button className="btn" onClick={() => setOpen(true)}><Plus size={16} /> New key</button>
      </div>

      <div className="toolbar">
        <div className="search">
          <Search size={16} />
          <input placeholder="Search keys…" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <span className="muted">{keys.filter((k) => k.active).length} active of {keys.length}</span>
      </div>

      <div className="key-grid">
        {shown.map((k) => (
          <div key={k.id} className={`card key-card ${k.active ? '' : 'inactive'}`}>
            <div className="key-top">
              <div className="key-icon"><KeyRound size={18} /></div>
              <div className="key-title">
                <b>{k.name}</b>
                <span className="muted">Created {k.createdAt} · {k.requests ?? 0} requests</span>
              </div>
              <Switch checked={k.active} onChange={() => handleToggle(k)} label={`Toggle ${k.name}`} />
            </div>

            <div className="key-value">
              <code>{mask(k.key)}</code>
              <button className="icon-btn" onClick={() => copy(k.key)} aria-label="Copy key"><Copy size={15} /></button>
            </div>

            <div className="key-stats">
              <div>
                <span className="muted">Rate limit</span>
                <b>{k.rateLimit} req/min</b>
              </div>
              <div>
                <span className="muted">Budget used</span>
                <b>${k.spent.toFixed(3)} / ${k.monthlyBudget}</b>
              </div>
            </div>
            <Progress value={k.spent} max={k.monthlyBudget} />

            <div className="key-foot">
              <span className={`chip ${k.active ? 'healthy' : 'off'}`}>{k.active ? 'Active' : 'Revoked'}</span>
              <button className="icon-btn danger" onClick={() => handleDelete(k)} aria-label="Delete key"><Trash2 size={16} /></button>
            </div>
          </div>
        ))}
        {shown.length === 0 && <p className="muted">No keys match "{query}".</p>}
      </div>

      {open && (
        <Modal title={created ? 'Key created' : 'Create API key'} onClose={close}>
          {created ? (
            <div className="form">
              <p className="muted">Copy this key now. For security it will be masked after you close this window.</p>
              <div className="key-value big">
                <code>{created.key}</code>
                <button className="icon-btn" onClick={() => copy(created.key)} aria-label="Copy key"><Copy size={16} /></button>
              </div>
              <button className="btn" onClick={close}>Done</button>
            </div>
          ) : (
            <form className="form" onSubmit={handleCreate}>
              <label>
                Name
                <input autoFocus placeholder="e.g. Mobile App" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </label>
              <div className="form-row">
                <label>
                  Rate limit (req/min)
                  <input type="number" min="1" value={form.rateLimit} onChange={(e) => setForm({ ...form, rateLimit: e.target.value })} />
                </label>
                <label>
                  Monthly budget ($)
                  <input type="number" min="0" step="0.5" value={form.monthlyBudget} onChange={(e) => setForm({ ...form, monthlyBudget: e.target.value })} />
                </label>
              </div>
              <div className="form-actions">
                <button type="button" className="ghost" onClick={close}>Cancel</button>
                <button className="btn" disabled={!form.name.trim()}>Create key</button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </div>
  );
}
