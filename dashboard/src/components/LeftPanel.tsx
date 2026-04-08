import { useState } from 'react';
import './LeftPanel.css';

const API_BASE = 'http://localhost:8000/api';

interface Props {
  status: Record<string, unknown>;
  connected: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  sleeping:  'var(--text-2)',
  watching:  'var(--blue)',
  analysing: 'var(--gold)',
  executing: 'var(--green)',
  paused:    'var(--amber)',
  shutdown:  'var(--red)',
};

function formatTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  } catch {
    return '—';
  }
}

function formatPnl(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}$${value.toFixed(2)}`;
}

export default function LeftPanel({ status, connected }: Props) {
  const [ctrlLoading, setCtrlLoading] = useState<string | null>(null);

  async function sendControl(action: string) {
    setCtrlLoading(action);
    try {
      await fetch(`${API_BASE}/control/${action}`, { method: 'POST' });
    } catch { /* silent */ } finally {
      setCtrlLoading(null);
    }
  }

  const state = String(status.status || 'unknown');
  const dotColor = STATUS_COLORS[state] || 'var(--text-3)';
  const statusLabel = state.charAt(0).toUpperCase() + state.slice(1);

  const currentWindow = String(status.current_window || '—');
  const sessionName = String(status.session_name || status.session || '—');
  const minutesIntoWindow = status.minutes_into_window !== undefined
    ? `${Number(status.minutes_into_window)}min`
    : '—';

  const dailyPnl = Number(status.daily_pnl || 0);
  const openPositions = status.open_positions !== undefined ? String(status.open_positions) : '0';
  const lastAnalysis = status.last_analysis_time
    ? formatTime(String(status.last_analysis_time))
    : '—';

  return (
    <div className="left-panel-inner">

      {/* AGENT */}
      <div className="lp-section">
        <div className="lp-section-label">Agent</div>
        <div className="lp-status-row">
          <span className="lp-status-dot" style={{ background: dotColor }} />
          <span className="lp-status-text" style={{ color: dotColor }}>{statusLabel}</span>
        </div>
        <div className="lp-row">
          <span className="lp-label">SYMBOL</span>
          <span className="lp-value">XAUUSDm</span>
        </div>
        <div className="lp-row">
          <span className="lp-label">MAGIC</span>
          <span className="lp-value">234001</span>
        </div>
      </div>

      {/* SESSION */}
      <div className="lp-section">
        <div className="lp-section-label">Session</div>
        <div className="lp-row">
          <span className="lp-label">WINDOW</span>
          <span className="lp-value">{currentWindow}</span>
        </div>
        <div className="lp-row">
          <span className="lp-label">SESSION</span>
          <span className="lp-value">{sessionName}</span>
        </div>
        <div className="lp-row">
          <span className="lp-label">IN WINDOW</span>
          <span className="lp-value">{minutesIntoWindow}</span>
        </div>
        <div className="lp-row">
          <span className="lp-label">CONNECTION</span>
          <span className={`lp-badge ${connected ? 'lp-badge-live' : 'lp-badge-offline'}`}>
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* ACCOUNT */}
      <div className="lp-section">
        <div className="lp-section-label">Account</div>
        <div className="lp-row">
          <span className="lp-label">DAILY P&L</span>
          <span className={`lp-value ${dailyPnl >= 0 ? 'lp-positive' : 'lp-negative'}`}>
            {formatPnl(dailyPnl)}
          </span>
        </div>
        <div className="lp-row">
          <span className="lp-label">OPEN POS.</span>
          <span className="lp-value">{openPositions}</span>
        </div>
        <div className="lp-row">
          <span className="lp-label">LAST SIGNAL</span>
          <span className="lp-value">{lastAnalysis}</span>
        </div>
      </div>

      {/* RISK */}
      <div className="lp-section">
        <div className="lp-section-label">Risk</div>
        <div className="lp-row">
          <span className="lp-label">MAX RISK</span>
          <span className="lp-value">2% per trade</span>
        </div>
        <div className="lp-row">
          <span className="lp-label">DAILY LIMIT</span>
          <span className="lp-value">6% drawdown</span>
        </div>
        <div className="lp-row">
          <span className="lp-label">SL RANGE</span>
          <span className="lp-value">8–50 pts</span>
        </div>
      </div>

      {/* CONTROLS */}
      <div className="lp-section">
        <div className="lp-section-label">Controls</div>
        <div className="lp-controls">
          <button
            className="lp-btn lp-btn-pause"
            onClick={() => sendControl('pause')}
            disabled={ctrlLoading !== null}
          >
            {ctrlLoading === 'pause' ? '...' : 'PAUSE'}
          </button>
          <button
            className="lp-btn lp-btn-resume"
            onClick={() => sendControl('resume')}
            disabled={ctrlLoading !== null}
          >
            {ctrlLoading === 'resume' ? '...' : 'RESUME'}
          </button>
        </div>
      </div>

    </div>
  );
}
