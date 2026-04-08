import { CheckCircle2, AlertCircle, MinusCircle, ShieldCheck, ShieldAlert } from 'lucide-react';
import './AnalysisPanel.css';

interface Props {
  decisions: Record<string, unknown>[];
}

const GRADE_CONFIG: Record<string, {
  icon: React.ReactNode;
  bg: string;
  color: string;
  border: string;
}> = {
  'A+': {
    icon: <CheckCircle2 size={13} />,
    bg: 'rgba(0, 214, 143, 0.07)',
    color: 'var(--accent-green)',
    border: 'rgba(0, 214, 143, 0.15)',
  },
  B: {
    icon: <AlertCircle size={13} />,
    bg: 'rgba(244, 183, 64, 0.07)',
    color: 'var(--accent-gold)',
    border: 'rgba(244, 183, 64, 0.15)',
  },
  SKIP: {
    icon: <MinusCircle size={13} />,
    bg: 'transparent',
    color: 'var(--text-muted)',
    border: 'var(--border)',
  },
};

export default function AnalysisPanel({ decisions }: Props) {
  return (
    <div className="analysis-panel">
      <div className="card-header">
        <span className="card-title">Agent Decisions</span>
        <span className="card-count">{decisions.length}</span>
      </div>

      {!decisions.length ? (
        <div className="empty-state">
          <MinusCircle size={20} strokeWidth={1.5} />
          <span>No decisions logged yet</span>
        </div>
      ) : (
        <div className="decisions-list">
          {decisions.slice(0, 8).map((d, i) => {
            const grade = String(d.grade || 'SKIP');
            const cfg = GRADE_CONFIG[grade] || GRADE_CONFIG.SKIP;
            const dir = String(d.direction || '—');
            const conf = Number(d.confidence || 0);
            const reasoning = String(d.reasoning || '').slice(0, 110);
            const time = d.timestamp
              ? new Date(String(d.timestamp)).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              : '—';
            const gptVerdict = d.gpt_verdict ? String(d.gpt_verdict).toLowerCase() : null;

            return (
              <div
                key={i}
                className="decision-row"
                style={{ background: cfg.bg, borderColor: cfg.border }}
              >
                <div className="decision-left">
                  <span className="grade-pill" style={{ color: cfg.color }}>
                    {cfg.icon}
                    <span>{grade}</span>
                  </span>
                  {dir !== '—' && (
                    <span className={`decision-dir dir-${dir.toLowerCase()}`}>{dir}</span>
                  )}
                </div>

                <div className="decision-center">
                  {reasoning && (
                    <p className="decision-reasoning">{reasoning}{reasoning.length >= 110 ? '…' : ''}</p>
                  )}
                </div>

                <div className="decision-right">
                  {conf > 0 && (
                    <span className="conf-value mono">{conf}%</span>
                  )}
                  {gptVerdict && (
                    <span className={`gpt-badge gpt-${gptVerdict}`}>
                      {gptVerdict === 'confirm'
                        ? <ShieldCheck size={10} />
                        : <ShieldAlert size={10} />}
                      <span>GPT</span>
                    </span>
                  )}
                  <span className="decision-time">{time}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
