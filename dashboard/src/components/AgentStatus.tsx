import { Moon, Eye, Brain, Zap, Pause, XCircle, HelpCircle, Wifi, WifiOff, Clock, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import './AgentStatus.css';

interface Props {
  status: Record<string, unknown>;
  connected: boolean;
}

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  sleeping:  { icon: <Moon size={16} />,     color: 'var(--status-sleeping)',  label: 'Sleeping'   },
  watching:  { icon: <Eye size={16} />,      color: 'var(--status-watching)',  label: 'Watching'   },
  analysing: { icon: <Brain size={16} />,    color: 'var(--status-analysing)', label: 'Analysing'  },
  executing: { icon: <Zap size={16} />,      color: 'var(--status-executing)', label: 'Executing'  },
  paused:    { icon: <Pause size={16} />,    color: 'var(--status-paused)',    label: 'Paused'     },
  shutdown:  { icon: <XCircle size={16} />,  color: 'var(--status-shutdown)',  label: 'Offline'    },
};

export default function AgentStatus({ status, connected }: Props) {
  const state = String(status.status || 'unknown');
  const cfg = STATUS_CONFIG[state] || { icon: <HelpCircle size={16} />, color: 'var(--text-muted)', label: state };
  const window = String(status.current_window || '—');
  const pnl = Number(status.daily_pnl || 0);
  const lastAnalysis = status.last_analysis_time
    ? new Date(String(status.last_analysis_time)).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '—';

  return (
    <div className="status-card">
      <div className="status-left">
        <div className="status-dot-wrap">
          <span className="status-dot" style={{ background: cfg.color }} />
          <span className="status-dot-ring" style={{ borderColor: cfg.color }} />
        </div>
        <div className="status-info">
          <div className="status-icon-label" style={{ color: cfg.color }}>
            {cfg.icon}
            <span className="status-label">{cfg.label}</span>
          </div>
          <span className="status-sub">XAUUSDm · MAGIC 234001</span>
        </div>
      </div>

      <div className="status-metrics">
        <div className="metric">
          <span className="metric-icon"><Clock size={12} /></span>
          <span className="metric-label">Window</span>
          <span className="metric-value">{window}</span>
        </div>
        <div className="metric-divider" />
        <div className="metric">
          <span className="metric-icon">
            {pnl >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          </span>
          <span className="metric-label">Daily P&L</span>
          <span className={`metric-value ${pnl >= 0 ? 'positive' : 'negative'}`}>
            {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
          </span>
        </div>
        <div className="metric-divider" />
        <div className="metric">
          <span className="metric-icon"><Activity size={12} /></span>
          <span className="metric-label">Last Analysis</span>
          <span className="metric-value mono">{lastAnalysis}</span>
        </div>
      </div>

      <div className={`conn-badge ${connected ? 'online' : 'offline'}`}>
        {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
        <span>{connected ? 'Live' : 'Disconnected'}</span>
      </div>
    </div>
  );
}
