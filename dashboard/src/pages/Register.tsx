import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import './Register.css';

const API_BASE = 'http://localhost:8000/api';
const TOKEN_KEY = 'apexgold_token';

export default function Register() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [inviteCode, setInviteCode] = useState(searchParams.get('invite') ?? '');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, invite_code: inviteCode }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Registration failed' })) as { detail?: string };
        throw new Error(data.detail || 'Registration failed. Please try again.');
      }
      const data = await res.json() as { access_token: string; role: string };
      localStorage.setItem(TOKEN_KEY, data.access_token);
      navigate(data.role === 'owner' ? '/monitor' : '/home', { replace: true });
      // force page reload so AuthProvider picks up the new token
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="register-page">
      <div className="register-card">
        <div className="register-brand">
          <span className="register-brand-apex">APEX</span>
          <span className="register-brand-gold">GOLD</span>
        </div>
        <h1 className="register-title">Create your account</h1>
        <p className="register-subtitle">You need a valid invite code to register.</p>

        <form className="register-form" onSubmit={handleSubmit} noValidate>
          <div className="register-field">
            <label className="register-label" htmlFor="name">Full Name</label>
            <input
              id="name"
              className="register-input"
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Your full name"
              required
            />
          </div>

          <div className="register-field">
            <label className="register-label" htmlFor="email">Email</label>
            <input
              id="email"
              className="register-input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>

          <div className="register-field">
            <label className="register-label" htmlFor="password">Password</label>
            <input
              id="password"
              className="register-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Choose a strong password"
              autoComplete="new-password"
              required
            />
          </div>

          <div className="register-field">
            <label className="register-label" htmlFor="invite">Invite Code</label>
            <input
              id="invite"
              className="register-input register-input-mono"
              type="text"
              value={inviteCode}
              onChange={e => setInviteCode(e.target.value)}
              placeholder="XXXXXXXXXXXXXXXX"
              required
            />
          </div>

          {error && <div className="register-error">{error}</div>}

          <button
            type="submit"
            className="register-submit"
            disabled={loading || !name || !email || !password || !inviteCode}
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="register-login-link">
          Already have an account?{' '}
          <Link to="/login" className="register-login-anchor">Sign in</Link>
        </p>
        <p className="register-apply-link">
          No invite code?{' '}
          <Link to="/apply" className="register-apply-anchor">Apply for access</Link>
        </p>
      </div>
    </div>
  );
}
