import { useState } from 'react';
import Modal from './Modal';
import './TradesTable.css';

interface Props {
  trades: Record<string, unknown>[];
}

// ── Formatters ────────────────────────────────────────────────────────────────

function formatPrice(val: unknown): string {
  const n = Number(val);
  if (isNaN(n) || val === null || val === undefined || val === '') return '—';
  return n.toFixed(2);
}

function formatPnl(val: unknown): string {
  const n = Number(val);
  if (isNaN(n) || val === null || val === undefined || val === '') return '—';
  const sign = n >= 0 ? '+' : '';
  return `${sign}$${n.toFixed(2)}`;
}

function formatTime(val: unknown): string {
  if (!val) return '—';
  try {
    const d = new Date(String(val));
    const mo  = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh  = String(d.getHours()).padStart(2, '0');
    const mm  = String(d.getMinutes()).padStart(2, '0');
    return `${mo}/${day} ${hh}:${mm}`;
  } catch { return '—'; }
}

function formatTimeFull(val: unknown): string {
  if (!val) return '—';
  try { return new Date(String(val)).toLocaleString(); } catch { return '—'; }
}

function str(v: unknown, fallback = '—'): string {
  const s = String(v ?? '').trim();
  return s || fallback;
}

// ── Badges ────────────────────────────────────────────────────────────────────

function DirBadge({ dir }: { dir: string }) {
  const isBuy = String(dir).toLowerCase() === 'buy';
  return (
    <span className={`dir-badge ${isBuy ? 'dir-badge-buy' : 'dir-badge-sell'}`}>
      {isBuy ? 'BUY' : 'SELL'}
    </span>
  );
}

function StatusPill({ status }: { status: string }) {
  const s = String(status).toLowerCase();
  let cls = 'status-pill-closed';
  if (s === 'open') cls = 'status-pill-open';
  else if (s === 'tp1' || s === 'tp1_hit') cls = 'status-pill-tp1';
  else if (s === 'sl' || s === 'stopped')  cls = 'status-pill-sl';
  return <span className={`status-pill ${cls}`}>{String(status).toUpperCase()}</span>;
}

// ── Trade detail modal ────────────────────────────────────────────────────────

function TradeDetail({ trade, onClose }: { trade: Record<string, unknown>; onClose: () => void }) {
  const dir        = str(trade.direction);
  const status     = str(trade.status, 'closed');
  const pnl        = Number(trade.profit_usd ?? 0);
  const pnlStr     = formatPnl(trade.profit_usd);
  const pnlClass   = pnl >= 0 ? 'val-green' : 'val-red';
  const isOpen     = status.toLowerCase() === 'open';

  const lots       = str(trade.lot_size);
  const entry      = str(trade.entry_price);
  const sl         = str(trade.sl_price ?? trade.sl_level);
  const tp1        = str(trade.tp1_price ?? trade.tp1_level);
  const tp2        = str(trade.tp2_price ?? trade.tp2_level);
  const exitPrice  = str(trade.exit_price);
  const exitReason = str(trade.exit_reason);
  const profitPips = str(trade.profit_pips);
  const accountType = str(trade.account_type);
  const ticketId   = str(trade.ticket_id);
  const openTime   = formatTimeFull(trade.timestamp_open);
  const closeTime  = formatTimeFull(trade.timestamp_close);

  const isBuy = dir.toLowerCase() === 'buy';
  const modalTitle = `Trade — ${dir.toUpperCase()} · ${isOpen ? 'OPEN' : pnlStr}`;

  return (
    <Modal title={modalTitle} onClose={onClose}>

      {/* Summary */}
      <div className="detail-section">
        <div className="detail-grid">
          <div className="detail-row">
            <span className="detail-row-label">Direction</span>
            <span className={`detail-row-val ${isBuy ? 'val-green' : 'val-red'}`}>
              {dir.toUpperCase()}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-row-label">Status</span>
            <span className={`detail-row-val ${isOpen ? 'val-blue' : ''}`}>
              {status.toUpperCase()}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-row-label">P&L</span>
            <span className={`detail-row-val ${pnlClass}`}>{pnlStr}</span>
          </div>
          <div className="detail-row">
            <span className="detail-row-label">Lot Size</span>
            <span className="detail-row-val">{lots}</span>
          </div>
          {profitPips !== '—' && (
            <div className="detail-row">
              <span className="detail-row-label">Profit (pts)</span>
              <span className={`detail-row-val ${Number(profitPips) >= 0 ? 'val-green' : 'val-red'}`}>
                {profitPips}
              </span>
            </div>
          )}
          {accountType !== '—' && (
            <div className="detail-row">
              <span className="detail-row-label">Account</span>
              <span className="detail-row-val">{accountType}</span>
            </div>
          )}
        </div>
      </div>

      <hr className="detail-divider" />

      {/* Levels */}
      <div className="detail-section">
        <div className="detail-section-label">Levels</div>
        <div className="detail-grid">
          <div className="detail-row">
            <span className="detail-row-label">Entry</span>
            <span className="detail-row-val val-gold">{formatPrice(trade.entry_price)}</span>
          </div>
          <div className="detail-row">
            <span className="detail-row-label">Stop Loss</span>
            <span className="detail-row-val val-red">{formatPrice(trade.sl_price ?? trade.sl_level)}</span>
          </div>
          <div className="detail-row">
            <span className="detail-row-label">TP1</span>
            <span className="detail-row-val val-green">{formatPrice(trade.tp1_price ?? trade.tp1_level)}</span>
          </div>
          {tp2 !== '—' && (
            <div className="detail-row">
              <span className="detail-row-label">TP2</span>
              <span className="detail-row-val val-green">{formatPrice(trade.tp2_price ?? trade.tp2_level)}</span>
            </div>
          )}
          {exitPrice !== '—' && (
            <div className="detail-row">
              <span className="detail-row-label">Exit Price</span>
              <span className="detail-row-val">{exitPrice}</span>
            </div>
          )}
          {exitReason !== '—' && (
            <div className="detail-row">
              <span className="detail-row-label">Exit Reason</span>
              <span className="detail-row-val">{exitReason}</span>
            </div>
          )}
        </div>
      </div>

      <hr className="detail-divider" />

      {/* Timing */}
      <div className="detail-section">
        <div className="detail-section-label">Timing</div>
        <div className="detail-grid">
          <div className="detail-row">
            <span className="detail-row-label">Opened</span>
            <span className="detail-row-val" style={{ fontFamily: 'var(--sans)', fontSize: 12 }}>
              {openTime}
            </span>
          </div>
          {!isOpen && (
            <div className="detail-row">
              <span className="detail-row-label">Closed</span>
              <span className="detail-row-val" style={{ fontFamily: 'var(--sans)', fontSize: 12 }}>
                {closeTime}
              </span>
            </div>
          )}
          {ticketId !== '—' && (
            <div className="detail-row">
              <span className="detail-row-label">Ticket ID</span>
              <span className="detail-row-val">{ticketId}</span>
            </div>
          )}
        </div>
      </div>

    </Modal>
  );
}

// ── Table rows ────────────────────────────────────────────────────────────────

function TradeRow({
  trade,
  showStatus,
  onClick,
}: {
  trade: Record<string, unknown>;
  showStatus: boolean;
  onClick: () => void;
}) {
  const dir    = String(trade.direction || '');
  const pnl    = Number(trade.profit_usd ?? 0);
  const pnlStr = formatPnl(trade.profit_usd);
  const pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
  const isOpen   = String(trade.status || '').toLowerCase() === 'open';

  return (
    <tr className={`trade-row-clickable${isOpen ? ' row-open' : ''}`} onClick={onClick}>
      <td><DirBadge dir={dir} /></td>
      <td>{formatPrice(trade.lot_size)}</td>
      <td>{formatPrice(trade.entry_price)}</td>
      <td>{formatPrice(trade.sl_level ?? trade.sl_price)}</td>
      <td>{formatPrice(trade.tp1_level ?? trade.tp1_price)}</td>
      <td className={pnlClass}>{pnlStr}</td>
      {showStatus && <td><StatusPill status={String(trade.status || 'closed')} /></td>}
      <td>{formatTime(trade.timestamp_open)}</td>
    </tr>
  );
}

function TableHead({ showStatus }: { showStatus: boolean }) {
  return (
    <thead>
      <tr>
        <th>DIR</th>
        <th>LOTS</th>
        <th>ENTRY</th>
        <th>SL</th>
        <th>TP1</th>
        <th>P&L</th>
        {showStatus && <th>STATUS</th>}
        <th>TIME</th>
      </tr>
    </thead>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────

export default function TradesTable({ trades }: Props) {
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);

  const openTrades = trades.filter(t => String(t.status || '').toLowerCase() === 'open');

  return (
    <div className="trades-table-wrap">
      <div className="trades-header">
        <span className="trades-header-title">Trade History</span>
        <span className="trades-count-badge">{trades.length}</span>
      </div>

      {openTrades.length > 0 && (
        <>
          <div className="trades-section-header">
            <span className="trades-section-label trades-section-label-gold">Open Positions</span>
            <span className="trades-section-count">{openTrades.length}</span>
          </div>
          <table className="trades-tbl">
            <TableHead showStatus={false} />
            <tbody>
              {openTrades.map((trade, i) => (
                <TradeRow
                  key={String(trade.id || i)}
                  trade={trade}
                  showStatus={false}
                  onClick={() => setSelected(trade)}
                />
              ))}
            </tbody>
          </table>
        </>
      )}

      <div className="trades-section-header">
        <span className="trades-section-label trades-section-label-muted">History</span>
        <span className="trades-section-count">{trades.length}</span>
      </div>

      {trades.length === 0 ? (
        <div className="trades-empty">No trades recorded</div>
      ) : (
        <table className="trades-tbl">
          <TableHead showStatus={true} />
          <tbody>
            {trades.map((trade, i) => (
              <TradeRow
                key={String(trade.id || i) + '-hist'}
                trade={trade}
                showStatus={true}
                onClick={() => setSelected(trade)}
              />
            ))}
          </tbody>
        </table>
      )}

      {selected && (
        <TradeDetail trade={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
