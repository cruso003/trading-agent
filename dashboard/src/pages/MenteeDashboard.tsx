import { useEffect, useState } from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './MenteeDashboard.css';

const API_BASE = 'http://localhost:8000/api';

interface Summary {
  win_rate?: number;
  total_trades?: number;
  total_pnl?: number;
  month_pnl?: number;
  agent_status?: string;
  next_session_minutes?: number;
}

interface Trade {
  id?: number;
  direction?: string;
  entry_price?: number;
  sl_level?: number;
  tp1_level?: number;
  lot_size?: number;
  profit_usd?: number;
  status?: string;
  timestamp_open?: string;
  timestamp_close?: string;
}

interface Decision {
  id?: number;
  timestamp?: string;
  grade?: string;
  direction?: string;
  confidence?: number;
  gpt_verdict?: string;
  reasoning?: string;
  skip_reason?: string;
}

function formatPnl(v: number | undefined): string {
  if (v === undefined || v === null) return '—';
  const sign = v >= 0 ? '+' : '';
  return `${sign}$${v.toFixed(2)}`;
}

function formatPct(v: number | undefined): string {
  if (v === undefined || v === null) return '—';
  return `${v.toFixed(1)}%`;
}

function formatNumber(v: number | undefined): string {
  if (v === undefined || v === null) return '—';
  return String(v);
}

function formatPrice(v: number | undefined): string {
  if (v === undefined || v === null) return '—';
  return `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatTime(v: string | undefined): string {
  if (!v) return '—';
  try {
    const d = new Date(v);
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${mo}/${day} ${hh}:${mm}`;
  } catch {
    return '—';
  }
}

function agentStatusText(s: string | undefined): string {
  if (!s) return 'unknown';
  if (s === 'watching') return 'monitoring the market';
  if (s === 'analysing') return 'analysing a potential setup';
  if (s === 'executing') return 'executing a trade';
  if (s === 'sleeping') return 'outside trading hours';
  return s;
}

function agentStatusClass(s: string | undefined): string {
  if (s === 'executing') return 'banner-green';
  if (s === 'analysing') return 'banner-gold';
  if (s === 'watching') return 'banner-blue';
  return 'banner-dim';
}

function formatNextSession(minutes: number | undefined): string {
  if (!minutes) return '';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h > 0) return `Next session in ${h}h ${m}m`;
  return `Next session in ${m}m`;
}

export default function MenteeDashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<Summary>({});
  const [trades, setTrades] = useState<Trade[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API_BASE}/analytics/summary`);
        if (res.ok) setSummary(await res.json() as Summary);
      } catch { /* silent */ }
      try {
        const res = await fetch(`${API_BASE}/trades?limit=10`);
        if (res.ok) setTrades(await res.json() as Trade[]);
      } catch { /* silent */ }
      try {
        const res = await fetch(`${API_BASE}/decisions?limit=3`);
        if (res.ok) setDecisions(await res.json() as Decision[]);
      } catch { /* silent */ }
    }
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  const monthPnl = summary.month_pnl ?? summary.total_pnl;
  const statusKey = summary.agent_status;

  return (
    <div className="mentee-page">
      <div className="mentee-inner">

        {/* Header */}
        <div className="mentee-header">
          <h1 className="mentee-greeting">
            Welcome back{user?.name ? `, ${user.name.split(' ')[0]}` : ''}.
          </h1>
          <p className="mentee-header-sub">Here's what the agent has been doing.</p>
        </div>

        {/* Stats strip */}
        <div className="mentee-stats">
          <div className="mentee-stat-card">
            <span className="mentee-stat-val mono">{formatPnl(monthPnl)}</span>
            <span className="mentee-stat-label">THIS MONTH P&L</span>
          </div>
          <div className="mentee-stat-card">
            <span className="mentee-stat-val mono">{formatPct(summary.win_rate)}</span>
            <span className="mentee-stat-label">WIN RATE</span>
          </div>
          <div className="mentee-stat-card">
            <span className="mentee-stat-val mono">{formatNumber(summary.total_trades)}</span>
            <span className="mentee-stat-label">TRADES</span>
          </div>
        </div>

        {/* Agent status banner */}
        <div className={`mentee-banner ${agentStatusClass(statusKey)}`}>
          <div className="mentee-banner-dot" />
          <div className="mentee-banner-text">
            <span className="mentee-banner-primary">
              Agent is currently <strong>{agentStatusText(statusKey)}</strong>
            </span>
            {statusKey === 'sleeping' && summary.next_session_minutes && (
              <span className="mentee-banner-secondary">
                {formatNextSession(summary.next_session_minutes)}
              </span>
            )}
          </div>
        </div>

        <div className="mentee-columns">

          {/* Recent signals */}
          <div className="mentee-section">
            <h2 className="mentee-section-title">Recent Signals</h2>
            {trades.length === 0 ? (
              <div className="mentee-empty">
                No trades yet. Agent is watching for setups.
              </div>
            ) : (
              <div className="mentee-signals">
                {trades.map((trade, i) => {
                  const isBuy = String(trade.direction || '').toUpperCase() === 'BUY';
                  const isOpen = String(trade.status || '').toLowerCase() === 'open';
                  const pnl = trade.profit_usd;
                  const hasPnl = pnl !== undefined && pnl !== null && !isOpen;

                  return (
                    <div className="mentee-signal-card" key={trade.id ?? i}>
                      <div className="mentee-signal-left">
                        <span className={`mentee-signal-icon ${isBuy ? 'icon-buy' : 'icon-sell'}`}>
                          {isBuy ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                        </span>
                        <div className="mentee-signal-info">
                          <p className="mentee-signal-main">
                            Agent {isBuy ? 'bought' : 'sold'} gold at {formatPrice(trade.entry_price)}
                          </p>
                          <p className="mentee-signal-detail">
                            Target: {formatPrice(trade.tp1_level)}
                            {' · '}Stop: {formatPrice(trade.sl_level)}
                            {trade.lot_size !== undefined && ` · Size: ${trade.lot_size} lots`}
                          </p>
                        </div>
                      </div>
                      <div className="mentee-signal-right">
                        {isOpen ? (
                          <span className="mentee-outcome-badge badge-active">Active</span>
                        ) : hasPnl ? (
                          <span className={`mentee-outcome-badge ${(pnl ?? 0) >= 0 ? 'badge-won' : 'badge-lost'}`}>
                            {(pnl ?? 0) >= 0 ? `Won ${formatPnl(pnl)}` : `Lost ${formatPnl(pnl)}`}
                          </span>
                        ) : (
                          <span className="mentee-outcome-badge badge-closed">Closed</span>
                        )}
                        <span className="mentee-signal-time">{formatTime(trade.timestamp_open)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Session analysis */}
          <div className="mentee-section">
            <h2 className="mentee-section-title">Session Analysis</h2>
            {decisions.length === 0 ? (
              <div className="mentee-empty">
                No session notes yet.
              </div>
            ) : (
              <div className="mentee-notes">
                {decisions.map((d, i) => {
                  const isSkip = d.grade === 'SKIP' || d.grade === 'skip' || d.grade === 'C';
                  const noteText = isSkip
                    ? `Agent skipped — ${d.skip_reason || (d.reasoning ? d.reasoning.slice(0, 80) : 'no setup found')}`
                    : `Agent identified a ${d.direction || 'neutral'} setup · ${d.confidence ?? '—'}% confidence · GPT ${d.gpt_verdict || '—'}`;

                  return (
                    <div className="mentee-note" key={d.id ?? i}>
                      <span className="mentee-note-time">{formatTime(d.timestamp)}</span>
                      <p className="mentee-note-text">{noteText}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
