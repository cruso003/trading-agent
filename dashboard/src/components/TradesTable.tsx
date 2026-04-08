import './TradesTable.css';

interface Props {
  trades: Record<string, unknown>[];
}

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
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${mo}/${day} ${hh}:${mm}`;
  } catch {
    return '—';
  }
}

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
  else if (s === 'sl' || s === 'stopped') cls = 'status-pill-sl';
  return (
    <span className={`status-pill ${cls}`}>{String(status).toUpperCase()}</span>
  );
}

function TradeRow({ trade, showStatus }: { trade: Record<string, unknown>; showStatus: boolean }) {
  const dir = String(trade.direction || '');
  const pnl = Number(trade.profit_usd ?? 0);
  const pnlStr = formatPnl(trade.profit_usd);
  const pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
  const isOpen = String(trade.status || '').toLowerCase() === 'open';

  return (
    <tr className={isOpen ? 'row-open' : ''}>
      <td><DirBadge dir={dir} /></td>
      <td>{formatPrice(trade.lot_size)}</td>
      <td>{formatPrice(trade.entry_price)}</td>
      <td>{formatPrice(trade.sl_level)}</td>
      <td>{formatPrice(trade.tp1_level)}</td>
      <td className={pnlClass}>{pnlStr}</td>
      {showStatus && (
        <td><StatusPill status={String(trade.status || 'closed')} /></td>
      )}
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

export default function TradesTable({ trades }: Props) {
  const openTrades = trades.filter(t => String(t.status || '').toLowerCase() === 'open');
  const allTrades = trades;

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
                <TradeRow key={String(trade.id || i)} trade={trade} showStatus={false} />
              ))}
            </tbody>
          </table>
        </>
      )}

      <div className="trades-section-header">
        <span className="trades-section-label trades-section-label-muted">History</span>
        <span className="trades-section-count">{allTrades.length}</span>
      </div>

      {allTrades.length === 0 ? (
        <div className="trades-empty">No trades recorded</div>
      ) : (
        <table className="trades-tbl">
          <TableHead showStatus={true} />
          <tbody>
            {allTrades.map((trade, i) => (
              <TradeRow key={String(trade.id || i) + '-hist'} trade={trade} showStatus={true} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
