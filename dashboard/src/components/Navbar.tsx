import { Link } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  function scrollTo(id: string) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <span className="navbar-brand-apex">APEX</span>
          <span className="navbar-brand-gold">GOLD</span>
        </Link>

        <nav className="navbar-nav">
          <button className="navbar-link" onClick={() => scrollTo('how-it-works')}>How It Works</button>
          <button className="navbar-link" onClick={() => scrollTo('performance')}>Performance</button>
          <button className="navbar-link" onClick={() => scrollTo('academy')}>Academy</button>
          <button className="navbar-link" onClick={() => scrollTo('mentorship')}>Mentorship</button>
        </nav>

        <div className="navbar-actions">
          <Link to="/login" className="navbar-btn-ghost">Login</Link>
          <Link to="/apply" className="navbar-btn-gold">Apply Now</Link>
        </div>
      </div>
    </header>
  );
}
