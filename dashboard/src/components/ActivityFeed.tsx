import { useState } from 'react';
import { ShieldCheck, ShieldAlert } from 'lucide-react';
import type { SSEEvent } from '../hooks/useSSE';
import Modal from './Modal';
import './ActivityFeed.css';

interface Props {
  decisions: Record<string, unknown>[];
  recentEvents: SSEEvent[];
}

// ── Formatters ────────────────────────────────────────────────────────────────

function formatDecTime(val: unknown): string {
  if (!val) return '—';
  try {
    const d = new Date(String(val));
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  } catch { return '—'; }
}

function formatDecTimeFull(val: unknown): string {
  if (!val) return '—';
  try {
    const d = new Date(String(val));
    return d.toLocaleString();
  } catch { return '—'; }
}

function formatEventTime(isoString: string | undefined): string {
  if (!isoString) return '--:--:--';
  try {
    const d = new Date(isoString);
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    const ss = String(d.getSeconds()).padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  } catch { return '--:--:--'; }
}

function str(v: unknown, fallback = '—'): string {
  const s = String(v ?? '').trim();
  return s || fallback;
}

// ── Badges ────────────────────────────────────────────────────────────────────

function GradeBadge({ grade }: { grade: string }) {
  const g = String(grade).toUpperCase();
  let cls = 'af-grade-skip';
  if (g === 'A+' || g === 'A') cls = 'af-grade-a';
  else if (g === 'B') cls = 'af-grade-b';
  return <span className={`af-grade-badge ${cls}`}>{g}</span>;
}

function DirBadge({ dir }: { dir: string }) {
  const d = String(dir || '').toLowerCase();
  if (d === 'buy') return <span className="af-dir-badge af-dir-buy">BUY</span>;
  if (d === 'sell') return <span className="af-dir-badge af-dir-sell">SELL</span>;
  return <span className="af-dir-none">—</span>;
}

function ModalGradeBadge({ grade }: { grade: string }) {
  const g = String(grade).toUpperCase();
  let cls = 'dg-skip';
  if (g === 'A+' || g === 'A') cls = 'dg-a';
  else if (g === 'B') cls = 'dg-b';
  return <span className={`detail-grade-badge ${cls}`}>{g}</span>;
}

// ── Decision detail modal ─────────────────────────────────────────────────────

function DecisionDetail({ dec, onClose }: { dec: Record<string, unknown>; onClose: () => void }) {
  const grade = str(dec.grade || dec.analysis_grade, 'SKIP');
  const dir   = str(dec.direction || dec.trade_direction);
  const conf  = dec.confidence !== undefined ? `${Number(dec.confidence)}%` : '—';
  const ts    = formatDecTimeFull(dec.timestamp || dec.created_at || dec.time);

  const entry      = str(dec.entry_price);
  const entryZone  = str(dec.entry_zone);
  const sl         = str(dec.sl_level);
  const tp1        = str(dec.tp1_level);
  const tp2        = str(dec.tp2_level);
  const inval      = str(dec.invalidation);

  const reasoning  = str(dec.reasoning || dec.rationale || dec.notes);
  const skipReason = str(dec.skip_reason);
  const execReason = str(dec.execution_reason);

  const pTrend    = str(dec.pillar_trend);
  const pMom      = str(dec.pillar_momentum);
  const pLoc      = str(dec.pillar_location);
  const setupType = str(dec.setup_type);
  const baseZone  = str(dec.base_zone);

  const gptVerdict  = str(dec.gpt_verdict);
  const gptReason   = str(dec.gpt_reasoning);
  const newsRisk    = str(dec.news_risk);
  const newsSummary = str(dec.news_summary);

  const executed  = Boolean(dec.executed);
  const window    = str(dec.window_name);

  const verdictOk = gptVerdict.toLowerCase() === 'confirm';

  const modalTitle = `Decision — ${grade} ${dir !== '—' ? dir.toUpperCase() : ''} · ${ts}`;

  return (
    <Modal title={modalTitle} onClose={onClose}>

      {/* Summary row */}
      <div className="detail-section">
        <div className="detail-grid" style={{ gridTemplateColumns: 'auto 1fr 1fr 1fr' }}>
          <div className="detail-row">
            <span className="detail-row-label">Grade</span>
            <span className="detail-row-val"><ModalGradeBadge grade={grade} /></span>
          </div>
          <div className="detail-row">
            <span className="detail-row-label">Direction</span>
            <span className={`detail-row-val ${dir.toLowerCase() === 'buy' ? 'val-green' : dir.toLowerCase() === 'sell' ? 'val-red' : ''}`}>
              {dir.toUpperCase()}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-row-label">Confidence</span>
            <span className="detail-row-val">{conf}</span>
          </div>
          <div className="detail-row">
            <span className="detail-row-label">Executed</span>
            <span className={`detail-row-val ${executed ? 'val-green' : ''}`}>
              {executed ? 'YES' : 'NO'}
            </span>
          </div>
        </div>
      </div>

      <hr className="detail-divider" />

      {/* Levels */}
      {(entry !== '—' || sl !== '—' || tp1 !== '—') && (
        <>
          <div className="detail-section">
            <div className="detail-section-label">Levels</div>
            <div className="detail-grid">
              <div className="detail-row">
                <span className="detail-row-label">Entry</span>
                <span className="detail-row-val val-gold">{entry}</span>
              </div>
              <div className="detail-row">
                <span className="detail-row-label">Entry Zone</span>
                <span className="detail-row-val">{entryZone}</span>
              </div>
              <div className="detail-row">
                <span className="detail-row-label">Stop Loss</span>
                <span className="detail-row-val val-red">{sl}</span>
              </div>
              <div className="detail-row">
                <span className="detail-row-label">TP1</span>
                <span className="detail-row-val val-green">{tp1}</span>
              </div>
              {tp2 !== '—' && (
                <div className="detail-row">
                  <span className="detail-row-label">TP2</span>
                  <span className="detail-row-val val-green">{tp2}</span>
                </div>
              )}
              {inval !== '—' && (
                <div className="detail-row">
                  <span className="detail-row-label">Invalidation</span>
                  <span className="detail-row-val">{inval}</span>
                </div>
              )}
            </div>
          </div>
          <hr className="detail-divider" />
        </>
      )}

      {/* Pillars */}
      {(pTrend !== '—' || pMom !== '—' || pLoc !== '—') && (
        <>
          <div className="detail-section">
            <div className="detail-section-label">Pillar Assessment</div>
            <div className="detail-grid">
              <div className="detail-row">
                <span className="detail-row-label">Trend</span>
                <span className="detail-row-val">{pTrend}</span>
              </div>
              <div className="detail-row">
                <span className="detail-row-label">Momentum</span>
                <span className="detail-row-val">{pMom}</span>
              </div>
              <div className="detail-row">
                <span className="detail-row-label">Location</span>
                <span className="detail-row-val">{pLoc}</span>
              </div>
              {setupType !== '—' && (
                <div className="detail-row">
                  <span className="detail-row-label">Setup Type</span>
                  <span className="detail-row-val">{setupType}</span>
                </div>
              )}
              {baseZone !== '—' && (
                <div className="detail-row">
                  <span className="detail-row-label">Base Zone</span>
                  <span className="detail-row-val">{baseZone}</span>
                </div>
              )}
              {window !== '—' && (
                <div className="detail-row">
                  <span className="detail-row-label">Window</span>
                  <span className="detail-row-val">{window}</span>
                </div>
              )}
            </div>
          </div>
          <hr className="detail-divider" />
        </>
      )}

      {/* Reasoning */}
      {reasoning !== '—' && (
        <>
          <div className="detail-section">
            <div className="detail-section-label">Reasoning</div>
            <div className="detail-grid detail-grid-1">
              <div className="detail-row">
                <span className="detail-row-val text-prose">{reasoning}</span>
              </div>
            </div>
          </div>
          <hr className="detail-divider" />
        </>
      )}

      {/* Skip / exec reason */}
      {(skipReason !== '—' || execReason !== '—') && (
        <>
          <div className="detail-section">
            <div className="detail-section-label">Outcome</div>
            <div className="detail-grid detail-grid-1">
              {skipReason !== '—' && (
                <div className="detail-row">
                  <span className="detail-row-label">Skip Reason</span>
                  <span className="detail-row-val text-prose">{skipReason}</span>
                </div>
              )}
              {execReason !== '—' && (
                <div className="detail-row">
                  <span className="detail-row-label">Execution Reason</span>
                  <span className="detail-row-val text-prose">{execReason}</span>
                </div>
              )}
            </div>
          </div>
          <hr className="detail-divider" />
        </>
      )}

      {/* GPT */}
      {gptVerdict !== '—' && (
        <>
          <div className="detail-section">
            <div className="detail-section-label">GPT Second Opinion</div>
            <div className="detail-grid">
              <div className="detail-row">
                <span className="detail-row-label">Verdict</span>
                <span className={`detail-row-val ${verdictOk ? 'val-green' : 'val-amber'}`}>
                  {gptVerdict.toUpperCase()}
                </span>
              </div>
            </div>
            {gptReason !== '—' && (
              <div className="detail-grid detail-grid-1" style={{ marginTop: 8 }}>
                <div className="detail-row">
                  <span className="detail-row-val text-prose">{gptReason}</span>
                </div>
              </div>
            )}
          </div>
          <hr className="detail-divider" />
        </>
      )}

      {/* News */}
      {newsRisk !== '—' && (
        <div className="detail-section">
          <div className="detail-section-label">News Context</div>
          <div className="detail-grid">
            <div className="detail-row">
              <span className="detail-row-label">Risk Level</span>
              <span className={`detail-row-val ${newsRisk === 'HIGH' ? 'val-red' : newsRisk === 'MEDIUM' ? 'val-amber' : ''}`}>
                {newsRisk}
              </span>
            </div>
            {newsSummary !== '—' && (
              <div className="detail-row">
                <span className="detail-row-label">Summary</span>
                <span className="detail-row-val text-prose">{newsSummary}</span>
              </div>
            )}
          </div>
        </div>
      )}

    </Modal>
  );
}

// ── Events tab ────────────────────────────────────────────────────────────────

function eventTypeClass(type: string): string {
  switch (type) {
    case 'trade_placed': case 'trade_closed': case 'tp1_hit': return 'ev-trade';
    case 'risk_blocked': case 'prefilter_fail':               return 'ev-risk';
    case 'analysis_done': case 'prefilter_pass':              return 'ev-info';
    case 'gpt_confirm':                                       return 'ev-gpt-confirm';
    case 'gpt_challenge':                                     return 'ev-gpt-challenge';
    case 'window_open':                                       return 'ev-window-open';
    case 'window_closed':                                     return 'ev-window-closed';
    default:                                                  return 'ev-faint';
  }
}

function eventSummary(event: SSEEvent): string {
  const d = event.data;
  const parts: string[] = [];
  if (d.symbol)    parts.push(String(d.symbol));
  if (d.direction) parts.push(String(d.direction).toUpperCase());
  if (d.reason)    parts.push(String(d.reason));
  if (d.message)   parts.push(String(d.message));
  if (d.window)    parts.push(String(d.window));
  return parts.slice(0, 3).join(' · ') || '';
}

// ── Main tabs ─────────────────────────────────────────────────────────────────

function DecisionsTab({ decisions }: { decisions: Record<string, unknown>[] }) {
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);

  if (decisions.length === 0) {
    return <div className="af-empty">No decisions recorded</div>;
  }

  return (
    <>
      {decisions.map((dec, i) => {
        const grade     = String(dec.grade || dec.analysis_grade || 'SKIP');
        const dir       = String(dec.direction || dec.trade_direction || '');
        const conf      = dec.confidence !== undefined ? `${Number(dec.confidence)}%` : null;
        const reasoning = String(dec.reasoning || dec.rationale || dec.notes || '');
        const skipReason = String(dec.skip_reason || '');
        const display   = (reasoning || skipReason).slice(0, 72);
        const truncated = display.length === 72 ? display + '…' : display;
        const hasVerdict = Boolean(dec.gpt_verdict);
        const verdictOk  = String(dec.gpt_verdict || '').toLowerCase() === 'confirm';
        const timestamp  = dec.timestamp || dec.created_at || dec.time;

        return (
          <div key={i} className="af-decision-row af-decision-clickable" onClick={() => setSelected(dec)}>
            <div className="af-decision-top">
              <span className="af-dec-time">{formatDecTime(timestamp)}</span>
              <GradeBadge grade={grade} />
              <DirBadge dir={dir} />
              {conf && <span className="af-conf">{conf}</span>}
              {hasVerdict && (
                <span className="af-verdict-icon">
                  {verdictOk
                    ? <ShieldCheck size={11} color="var(--green)" />
                    : <ShieldAlert size={11} color="var(--amber)" />
                  }
                </span>
              )}
              <span className="af-expand-hint">↗</span>
            </div>
            {truncated && <div className="af-decision-reason">{truncated}</div>}
          </div>
        );
      })}

      {selected && (
        <DecisionDetail dec={selected} onClose={() => setSelected(null)} />
      )}
    </>
  );
}

function EventsTab({ events }: { events: SSEEvent[] }) {
  const filtered = events.filter(e => e.type !== 'heartbeat');
  if (filtered.length === 0) {
    return <div className="af-empty">Waiting for events...</div>;
  }
  return (
    <div className="af-events-list">
      {filtered.map((ev, i) => (
        <div key={i} className="af-event-row">
          <span className="af-event-time">{formatEventTime(ev.timestamp)}</span>
          <span className={`af-event-type ${eventTypeClass(ev.type)}`}>
            [{ev.type.toUpperCase()}]
          </span>
          <span className="af-event-body">{eventSummary(ev)}</span>
        </div>
      ))}
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────

export default function ActivityFeed({ decisions, recentEvents }: Props) {
  const [activeTab, setActiveTab] = useState<'decisions' | 'events'>('decisions');

  return (
    <div className="activity-feed">
      <div className="af-header">
        <span className="af-title">Activity</span>
        <span className="af-live-dot" />
      </div>

      <div className="af-tabs">
        <button
          className={`af-tab${activeTab === 'decisions' ? ' active' : ''}`}
          onClick={() => setActiveTab('decisions')}
        >
          Decisions
        </button>
        <button
          className={`af-tab${activeTab === 'events' ? ' active' : ''}`}
          onClick={() => setActiveTab('events')}
        >
          Events
        </button>
      </div>

      <div className="af-content">
        {activeTab === 'decisions'
          ? <DecisionsTab decisions={decisions} />
          : <EventsTab events={recentEvents} />
        }
      </div>
    </div>
  );
}
