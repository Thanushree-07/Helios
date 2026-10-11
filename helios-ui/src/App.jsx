import { NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { Activity, KeyRound, LayoutDashboard, RotateCcw, ScrollText, Server, Sun, Terminal } from 'lucide-react';
import Dashboard from './pages/Dashboard.jsx';
import Playground from './pages/Playground.jsx';
import ApiKeys from './pages/ApiKeys.jsx';
import Providers from './pages/Providers.jsx';
import Logs from './pages/Logs.jsx';
import { resetDemoData } from './api.js';

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/playground', label: 'Playground', icon: Terminal },
  { to: '/keys', label: 'API Keys', icon: KeyRound },
  { to: '/providers', label: 'Providers', icon: Server },
  { to: '/logs', label: 'Request Logs', icon: ScrollText },
];

export default function App() {
  const { pathname } = useLocation();
  const current = links.find((l) => l.to === pathname) ?? links[0];

  function handleReset() {
    if (!confirm('Reset all demo data?')) return;
    resetDemoData();
    window.location.reload();
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo"><Sun size={20} /></div>
          <div>
            <h1>Helios</h1>
            <p>LLM Gateway</p>
          </div>
        </div>
        <nav>
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="endpoint">
            <span className="muted">Endpoint</span>
            <code>/v1/chat/completions</code>
          </div>
          <button className="ghost" onClick={handleReset}><RotateCcw size={14} /> Reset demo data</button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="crumb">
            <span className="muted">Helios /</span> {current.label}
          </div>
          <div className="topbar-right">
            <span className="pill live"><Activity size={14} /> Gateway online</span>
            <span className="pill">3 instances · Nginx LB</span>
            <div className="avatar">AD</div>
          </div>
        </header>
        <main className="content" key={pathname}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/playground" element={<Playground />} />
            <Route path="/keys" element={<ApiKeys />} />
            <Route path="/providers" element={<Providers />} />
            <Route path="/logs" element={<Logs />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
