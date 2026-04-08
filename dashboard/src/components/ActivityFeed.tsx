import { useState } from 'react';
import { ShieldCheck, ShieldAlert } from 'lucide-react';
import type { SSEEvent } from '../hooks/useSSE';
import './ActivityFeed.css';

interface Props {
  decisions: Record<string, unknown>[];
  recentEvents: SSEEvent[];
}

function formatDecTime(val: unknown): string {
  if (!val) return '—';
  try {
    const d = new Date(String(val));
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  } catch {
    return '—';
  }
}

function formatEventTime(isoString: string | undefined): string {
  if (!isoString) return '--:--:--';
  try {
    const d = new Date(isoString);
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    const ss = String(d.getSeconds()).padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  } catch {
    return '--:--:--';
  }
}

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

function eventTypeClass(type: string): string {
  switch (type) {
    case 'trade_placed':
    case 'trade_closed':
    case 'tp1_hit':
      return 'ev-trade';
    case 'risk_blocked':
    case 'prefilter_fail':
      return 'ev-risk';
    case 'analysis_done':
    case 'prefilter_pass':
      return 'ev-info';
    case 'gpt_confirm':
      return 'ev-gpt-confirm';
    case 'gpt_challenge':
      return 'ev-gpt-challenge';
    case 'window_open':
      return 'ev-window-open';
    case 'window_closed':
      return 'ev-window-closed';
    default:
      return 'ev-faint';
  }
}

function eventSummary(event: SSEEvent): string {
  const d = event.data;
  const parts: string[] = [];
  if (d.symbol) parts.push(String(d.symbol));
  if (d.direction) parts.push(String(d.direction).toUpperCase());
  if (d.reason) parts.push(String(d.reason));
  if (d.message) parts.push(String(d.message));
  if (d.window) parts.push(String(d.window));
  return parts.slice(0, 3).join(' · ') || '';
}

function DecisionsTab({ decisions }: { decisions: Record<string, unknown>[] }) {
  if (decisions.length === 0) {
    return <div className="af-empty">No decisions recorded</div>;
  }
  return (
    <>
      {decisions.map((dec, i) => {
        const grade = String(dec.grade || dec.analysis_grade || 'SKIP');
        const dir = String(dec.direction || dec.trade_direction || '');
        const conf = dec.confidence !== undefined ? `${Number(dec.confidence)}%` : null;
        const reasoning = String(dec.reasoning || dec.rationale || dec.notes || '');
        const truncated = reasoning.length > 80 ? reasoning.slice(0, 80) + '…' : reasoning;
        const hasVerdict = Boolean(dec.gpt_verdict);
        const verdictOk = String(dec.gpt_verdict || '').toLowerCase() === 'confirm';
        const timestamp = dec.timestamp || dec.created_at || dec.time;

        return (
          <div key={i} className="af-decision-row">
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
            </div>
            {truncated && (
              <div className="af-decision-reason">{truncated}</div>
            )}
          </div>
        );
      })}
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
