import { useState } from 'react';
import './Controls.css';

const API_BASE = 'http://localhost:8000/api';

export default function Controls() {
  const [loading, setLoading] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  async function sendControl(action: string) {
    setLoading(action);
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/control/${action}`, { method: 'POST' });
      const data = await res.json();
      setMessage(`${action}: ${data.status || 'OK'}`);
    } catch {
      setMessage(`${action} failed — API unreachable`);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="controls-card">
      <h3>Controls</h3>
      <div className="controls-grid">
        <button
          className="ctrl-btn pause"
          onClick={() => sendControl('pause')}
          disabled={loading !== null}
        >
          {loading === 'pause' ? '...' : '⏸️ Pause'}
        </button>
        <button
          className="ctrl-btn resume"
          onClick={() => sendControl('resume')}
          disabled={loading !== null}
        >
          {loading === 'resume' ? '...' : '▶️ Resume'}
        </button>
      </div>
      {message && <p className="ctrl-message">{message}</p>}
    </div>
  );
}
