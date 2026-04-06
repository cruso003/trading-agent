import './AgentStatus.css';

interface Props {
  status: Record<string, unknown>;
  connected: boolean;
}

const STATUS_CONFIG: Record<string, { emoji: string; color: string; label: string }> = {
  sleeping: { emoji: '😴', color: 'var(--status-sleeping)', label: 'Sleeping' },
  watching: { emoji: '👁️', color: 'var(--status-watching)', label: 'Watching' },
  analysing: { emoji: '🧠', color: 'var(--status-analysing)', label: 'Analysing' },
  executing: { emoji: '⚡', color: 'var(--status-executing)', label: 'Executing' },
  paused: { emoji: '⏸️', color: 'var(--status-paused)', label: 'Paused' },
  shutdown: { emoji: '🔴', color: 'var(--status-shutdown)', label: 'Offline' },
};

export default function AgentStatus({ status, connected }: Props) {
  const state = String(status.status || 'unknown');
  const cfg = STATUS_CONFIG[state] || { emoji: '❓', color: '#666', label: state };
  const window = String(status.current_window || '—');
  const pnl = Number(status.daily_pnl || 0);
  const lastAnalysis = status.last_analysis_time ? new Date(String(status.last_analysis_time)).toLocaleTimeString() : '—';

  return (
    <div className="agent-status-card">
      <div className="status-header">
        <div className="status-indicator">
          <span className="pulse" style={{ backgroundColor: cfg.color }} />
          <span className="status-emoji">{cfg.emoji}</span>
          <span className="status-label" style={{ color: cfg.color }}>{cfg.label}</span>
        </div>
        <div className={`connection-badge ${connected ? 'online' : 'offline'}`}>
          {connected ? '● LIVE' : '○ DISCONNECTED'}
        </div>
      </div>

      <div className="status-grid">
        <div className="stat-item">
          <span className="stat-label">Window</span>
          <span className="stat-value">{window}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Daily P&L</span>
          <span className={`stat-value ${pnl >= 0 ? 'positive' : 'negative'}`}>
            ${pnl.toFixed(2)}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Last Analysis</span>
          <span className="stat-value">{lastAnalysis}</span>
        </div>
      </div>
    </div>
  );
}
