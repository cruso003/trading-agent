import { useState } from 'react';
import { Pause, Play, Loader2 } from 'lucide-react';
import './Controls.css';

const API_BASE = 'http://localhost:8000/api';

export default function Controls() {
  const [loading, setLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

  async function sendControl(action: string) {
    setLoading(action);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/control/${action}`, { method: 'POST' });
      const data = await res.json();
      setMessage({ text: data.status || 'OK', ok: true });
    } catch {
      setMessage({ text: 'API unreachable', ok: false });
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="controls-card">
      <span className="controls-label">Agent Control</span>
      <div className="controls-row">
        <button
          className="ctrl-btn pause"
          onClick={() => sendControl('pause')}
          disabled={loading !== null}
        >
          {loading === 'pause'
            ? <Loader2 size={14} className="spin" />
            : <Pause size={14} />}
          <span>Pause</span>
        </button>
        <button
          className="ctrl-btn resume"
          onClick={() => sendControl('resume')}
          disabled={loading !== null}
        >
          {loading === 'resume'
            ? <Loader2 size={14} className="spin" />
            : <Play size={14} />}
          <span>Resume</span>
        </button>
      </div>
      {message && (
        <p className={`ctrl-message ${message.ok ? 'ok' : 'err'}`}>{message.text}</p>
      )}
    </div>
  );
}
