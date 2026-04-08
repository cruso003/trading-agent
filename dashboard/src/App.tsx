import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { LayoutDashboard, BarChart3, Zap } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import './App.css';

function UtcClock() {
  const [time, setTime] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const hh = String(now.getUTCHours()).padStart(2, '0');
      const mm = String(now.getUTCMinutes()).padStart(2, '0');
      const ss = String(now.getUTCSeconds()).padStart(2, '0');
      setTime(`${hh}:${mm}:${ss}`);
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="nav-clock">
      <span className="nav-clock-label">UTC</span>
      <span className="nav-clock-time mono">{time}</span>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-icon"><Zap size={14} /></span>
            <div className="topbar-brand">
              <span className="topbar-name mono">GOLDTRADER</span>
              <span className="topbar-sub">XAUUSD</span>
            </div>
            <div className="topbar-divider" />
            <nav className="topbar-nav">
              <NavLink
                to="/"
                end
                className={({ isActive }) => `topbar-link${isActive ? ' active' : ''}`}
              >
                <LayoutDashboard size={13} />
                <span>Monitor</span>
              </NavLink>
              <NavLink
                to="/analytics"
                className={({ isActive }) => `topbar-link${isActive ? ' active' : ''}`}
              >
                <BarChart3 size={13} />
                <span>Analytics</span>
              </NavLink>
            </nav>
          </div>

          <div className="topbar-right">
            <UtcClock />
          </div>
        </header>

        <main className="app-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
