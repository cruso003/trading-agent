import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BarChart3,
  Users,
  Megaphone,
  Home,
  TrendingUp,
  GraduationCap,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './AppShell.css';

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
    <div className="shell-clock">
      <span className="shell-clock-label">UTC</span>
      <span className="shell-clock-time mono">{time}</span>
    </div>
  );
}

interface Props {
  children: React.ReactNode;
}

export default function AppShell({ children }: Props) {
  const { user, logout, isOwner } = useAuth();

  return (
    <div className="shell">
      <header className="shell-topbar">
        <div className="shell-topbar-left">
          <div className="shell-brand">
            <span className="shell-brand-apex">APEX</span>
            <span className="shell-brand-gold">GOLD</span>
          </div>
          <div className="shell-divider" />
          <nav className="shell-nav">
            {isOwner ? (
              <>
                <NavLink
                  to="/monitor"
                  className={({ isActive }) => `shell-link${isActive ? ' active' : ''}`}
                >
                  <LayoutDashboard size={13} />
                  <span>Monitor</span>
                </NavLink>
                <NavLink
                  to="/analytics"
                  className={({ isActive }) => `shell-link${isActive ? ' active' : ''}`}
                >
                  <BarChart3 size={13} />
                  <span>Analytics</span>
                </NavLink>
                <NavLink
                  to="/manage"
                  className={({ isActive }) => `shell-link${isActive ? ' active' : ''}`}
                >
                  <Users size={13} />
                  <span>Manage</span>
                </NavLink>
                <NavLink
                  to="/broadcasts"
                  className={({ isActive }) => `shell-link${isActive ? ' active' : ''}`}
                >
                  <Megaphone size={13} />
                  <span>Broadcasts</span>
                </NavLink>
              </>
            ) : (
              <>
                <NavLink
                  to="/home"
                  className={({ isActive }) => `shell-link${isActive ? ' active' : ''}`}
                >
                  <Home size={13} />
                  <span>Home</span>
                </NavLink>
                <NavLink
                  to="/signals"
                  className={({ isActive }) => `shell-link${isActive ? ' active' : ''}`}
                >
                  <TrendingUp size={13} />
                  <span>Signals</span>
                </NavLink>
                <NavLink
                  to="/academy"
                  className={({ isActive }) => `shell-link${isActive ? ' active' : ''}`}
                >
                  <GraduationCap size={13} />
                  <span>Academy</span>
                </NavLink>
              </>
            )}
          </nav>
        </div>

        <div className="shell-topbar-right">
          <UtcClock />
          {user && (
            <span className="shell-username">{user.name}</span>
          )}
          <button className="shell-logout" onClick={logout} title="Logout">
            <LogOut size={14} />
          </button>
        </div>
      </header>

      <main className="shell-content">
        {children}
      </main>
    </div>
  );
}
