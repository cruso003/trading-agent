import { useEffect, useState, useCallback } from 'react';
import type { FormEvent } from 'react';
import { Megaphone, Send, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Broadcasts.css';

const API_BASE = 'http://localhost:8000/api';

interface Broadcast {
  id: number;
  title: string;
  message: string;
  owner_note?: string;
  trade_context?: string;
  created_at: string;
}

function formatDate(v: string): string {
  try {
    const d = new Date(v);
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${mo}/${day} ${hh}:${mm}`;
  } catch { return '—'; }
}

export default function Broadcasts() {
  const { token, isOwner } = useAuth();
  const [broadcasts, setBroadcasts] = useState<Broadcast[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  // Compose form (owner only)
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [ownerNote, setOwnerNote] = useState('');
  const [tradeContext, setTradeContext] = useState('');
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState('');
  const [sent, setSent] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/broadcasts`, { headers });
      if (res.ok) {
        const d = await res.json() as { broadcasts: Broadcast[] };
        setBroadcasts(d.broadcasts ?? []);
      }
    } catch { /* silent */ } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, refreshKey]);

  useEffect(() => { load(); }, [load]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    setSendError('');
    setSending(true);
    setSent(false);
    try {
      const res = await fetch(`${API_BASE}/broadcasts`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          message,
          owner_note: ownerNote || null,
          trade_context: tradeContext || null,
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({ detail: 'Failed' })) as { detail?: string };
        throw new Error(d.detail || 'Failed to send broadcast');
      }
      setSent(true);
      setTitle('');
      setMessage('');
      setOwnerNote('');
      setTradeContext('');
      setRefreshKey(k => k + 1);
      setTimeout(() => setSent(false), 3000);
    } catch (err) {
      setSendError(err instanceof Error ? err.message : 'Failed to send');
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="bc-page">
      <div className="bc-inner">
        <div className="bc-header">
          <h1 className="bc-title">Broadcasts</h1>
          <button className="bc-refresh" onClick={() => setRefreshKey(k => k + 1)} title="Refresh">
            <RefreshCw size={14} />
          </button>
        </div>

        <div className="bc-layout">

          {/* Compose (owner only) */}
          {isOwner && (
            <div className="bc-compose-panel">
              <div className="bc-compose-header">
                <Megaphone size={14} />
                <span>New Broadcast</span>
              </div>

              <form className="bc-compose-form" onSubmit={handleSend} noValidate>
                <div className="bc-field">
                  <label className="bc-label">Title</label>
                  <input
                    className="bc-input"
                    type="text"
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    placeholder="e.g. Asia Setup Update"
                    required
                  />
                </div>

                <div className="bc-field">
                  <label className="bc-label">Message</label>
                  <textarea
                    className="bc-input bc-textarea"
                    value={message}
                    onChange={e => setMessage(e.target.value)}
                    placeholder="Write your broadcast message..."
                    rows={4}
                    required
                  />
                </div>

                <div className="bc-field">
                  <label className="bc-label">
                    Trade Context
                    <span className="bc-field-optional">optional</span>
                  </label>
                  <input
                    className="bc-input"
                    type="text"
                    value={tradeContext}
                    onChange={e => setTradeContext(e.target.value)}
                    placeholder="e.g. BUY XAUUSDm @ 3088"
                  />
                </div>

                <div className="bc-field">
                  <label className="bc-label">
                    Owner Note
                    <span className="bc-field-optional">optional — for your records</span>
                  </label>
                  <input
                    className="bc-input"
                    type="text"
                    value={ownerNote}
                    onChange={e => setOwnerNote(e.target.value)}
                    placeholder="Private note visible to you only"
                  />
                </div>

                {sendError && <div className="bc-error">{sendError}</div>}
                {sent && <div className="bc-success">Broadcast sent.</div>}

                <button
                  type="submit"
                  className="bc-send-btn"
                  disabled={sending || !title || !message}
                >
                  <Send size={13} />
                  {sending ? 'Sending...' : 'Send to All Mentees'}
                </button>
              </form>
            </div>
          )}

          {/* Feed */}
          <div className="bc-feed">
            {loading ? (
              <div className="bc-empty">Loading...</div>
            ) : broadcasts.length === 0 ? (
              <div className="bc-empty">No broadcasts yet.</div>
            ) : (
              broadcasts.map(bc => (
                <div className="bc-card" key={bc.id}>
                  {bc.trade_context && (
                    <div className="bc-trade-context mono">{bc.trade_context}</div>
                  )}
                  <div className="bc-card-title">{bc.title}</div>
                  <p className="bc-card-message">{bc.message}</p>
                  {bc.owner_note && isOwner && (
                    <div className="bc-card-note">
                      <span className="bc-note-label">Note:</span> {bc.owner_note}
                    </div>
                  )}
                  <div className="bc-card-time">{formatDate(bc.created_at)}</div>
                </div>
              ))
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
