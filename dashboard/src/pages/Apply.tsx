import { useState } from 'react';
import type { FormEvent, ChangeEvent } from 'react';
import { Link } from 'react-router-dom';
import './Apply.css';

const API_BASE = 'http://localhost:8000/api';
const MAX_WHY_LENGTH = 500;

interface ApplyPayload {
  name: string;
  email: string;
  country: string;
  experience: string;
  reason: string;
}

export default function Apply() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [country, setCountry] = useState('');
  const [experience, setExperience] = useState('');
  const [why, setWhy] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    const payload: ApplyPayload = { name, email, country, experience, reason: why };

    try {
      const res = await fetch(`${API_BASE}/auth/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Submission failed' })) as { detail?: string };
        throw new Error(data.detail || 'Submission failed. Please try again.');
      }

      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function handleWhyChange(e: ChangeEvent<HTMLTextAreaElement>) {
    if (e.target.value.length <= MAX_WHY_LENGTH) {
      setWhy(e.target.value);
    }
  }

  if (submitted) {
    return (
      <div className="apply-page">
        <div className="apply-card">
          <div className="apply-brand">
            <span className="apply-brand-apex">APEX</span>
            <span className="apply-brand-gold">GOLD</span>
          </div>
          <div className="apply-success">
            <div className="apply-success-title">Application received.</div>
            <p className="apply-success-body">
              We'll review your application and reach out via email within 48 hours.
              Only successful applicants receive an invite to register.
            </p>
          </div>
          <p className="apply-back">
            <Link to="/" className="apply-back-link">Back to home</Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="apply-page">
      <div className="apply-card">
        <div className="apply-brand">
          <span className="apply-brand-apex">APEX</span>
          <span className="apply-brand-gold">GOLD</span>
        </div>
        <h1 className="apply-title">Apply for Mentorship Access</h1>
        <p className="apply-subtitle">
          Tell us about yourself. Applications are reviewed manually within 48 hours.
        </p>

        <form className="apply-form" onSubmit={handleSubmit} noValidate>
          <div className="apply-field">
            <label className="apply-label" htmlFor="name">Full Name</label>
            <input
              id="name"
              className="apply-input"
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Your full name"
              required
            />
          </div>

          <div className="apply-field">
            <label className="apply-label" htmlFor="email">Email</label>
            <input
              id="email"
              className="apply-input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>

          <div className="apply-field">
            <label className="apply-label" htmlFor="country">Country</label>
            <input
              id="country"
              className="apply-input"
              type="text"
              value={country}
              onChange={e => setCountry(e.target.value)}
              placeholder="e.g. United Kingdom"
              required
            />
          </div>

          <div className="apply-field">
            <label className="apply-label" htmlFor="experience">Trading Experience</label>
            <select
              id="experience"
              className="apply-input apply-select"
              value={experience}
              onChange={e => setExperience(e.target.value)}
              required
            >
              <option value="" disabled>Select your experience level</option>
              <option value="none">No experience</option>
              <option value="beginner">Some experience (&lt; 1 year)</option>
              <option value="intermediate">Intermediate (1–3 years)</option>
            </select>
          </div>

          <div className="apply-field">
            <label className="apply-label" htmlFor="why">
              Why do you want to join?
              <span className="apply-char-count">{why.length}/{MAX_WHY_LENGTH}</span>
            </label>
            <textarea
              id="why"
              className="apply-input apply-textarea"
              value={why}
              onChange={handleWhyChange}
              placeholder="Tell us what you're looking for and what you hope to achieve..."
              rows={4}
              required
            />
          </div>

          {error && <div className="apply-error">{error}</div>}

          <button
            type="submit"
            className="apply-submit"
            disabled={loading || !name || !email || !country || !experience || !why}
          >
            {loading ? 'Submitting...' : 'Submit Application'}
          </button>
        </form>

        <p className="apply-login-link">
          Already have access?{' '}
          <Link to="/login" className="apply-login-anchor">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
