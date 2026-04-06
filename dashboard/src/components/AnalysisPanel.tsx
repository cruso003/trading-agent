import './AnalysisPanel.css';

interface Props {
  decisions: Record<string, unknown>[];
}

const GRADE_CONFIG: Record<string, { emoji: string; bg: string; color: string }> = {
  'A+': { emoji: '🟢', bg: 'rgba(0, 255, 136, 0.1)', color: 'var(--accent-green)' },
  B: { emoji: '🟡', bg: 'rgba(255, 201, 71, 0.1)', color: 'var(--accent-gold)' },
  SKIP: { emoji: '⚪', bg: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-muted)' },
};

export default function AnalysisPanel({ decisions }: Props) {
  return (
    <div className="analysis-panel">
      <h3>Recent Decisions</h3>

      {!decisions.length && (
        <p className="empty-state">No decisions logged yet.</p>
      )}

      <div className="decisions-list">
        {decisions.slice(0, 8).map((d, i) => {
          const grade = String(d.grade || 'SKIP');
          const cfg = GRADE_CONFIG[grade] || GRADE_CONFIG.SKIP;
          const dir = String(d.direction || '—');
          const conf = Number(d.confidence || 0);
          const reasoning = String(d.reasoning || '').slice(0, 120);
          const time = d.timestamp
            ? new Date(String(d.timestamp)).toLocaleTimeString()
            : '—';

          return (
            <div key={i} className="decision-item" style={{ background: cfg.bg }}>
              <div className="decision-header">
                <span className="grade-badge" style={{ color: cfg.color }}>
                  {cfg.emoji} {grade}
                </span>
                <span className="decision-dir">{dir}</span>
                <span className="decision-conf">{conf}%</span>
                <span className="decision-time">{time}</span>
              </div>
              {reasoning && (
                <p className="decision-reasoning">{reasoning}...</p>
              )}
              {Boolean(d.gpt_verdict) && (
                <span className={`gpt-badge ${String(d.gpt_verdict).toLowerCase()}`}>
                  GPT: {String(d.gpt_verdict)}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
