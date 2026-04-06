import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="sidebar">
          <div className="logo">
            <span className="logo-icon">⚡</span>
            <span className="logo-text">GoldTrader</span>
          </div>
          <div className="nav-links">
            <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">📊</span>
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">📈</span>
              <span>Analytics</span>
            </NavLink>
          </div>
          <div className="sidebar-footer">
            <span className="version">v1.0.0</span>
          </div>
        </nav>

        <main className="content">
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
