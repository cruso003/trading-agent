import './TradeCard.css';

interface Props {
  trades: Record<string, unknown>[];
}

export default function TradeCard({ trades }: Props) {
  if (!trades.length) {
    return (
      <div className="trade-card empty">
        <h3>Recent Trades</h3>
        <p className="empty-state">No trades yet. Agent is watching for setups.</p>
      </div>
    );
  }

  return (
    <div className="trade-card">
      <h3>Recent Trades</h3>
      <div className="trades-list">
        {trades.slice(0, 10).map((trade, i) => {
          const dir = String(trade.direction || '');
          const profit = Number(trade.profit_usd || 0);
          const entry = Number(trade.entry_price || 0);
          const lots = Number(trade.lot_size || 0);
          const time = trade.timestamp_open
            ? new Date(String(trade.timestamp_open)).toLocaleString()
            : '—';

          return (
            <div key={i} className={`trade-item ${dir.toLowerCase()}`}>
              <div className="trade-direction">
                <span className={`dir-badge ${dir.toLowerCase()}`}>{dir}</span>
                <span className="trade-lots">{lots} lots</span>
              </div>
              <div className="trade-details">
                <span className="trade-entry">@ {entry.toFixed(2)}</span>
                <span className="trade-time">{time}</span>
              </div>
              <div className={`trade-pnl ${profit >= 0 ? 'win' : 'loss'}`}>
                {profit >= 0 ? '+' : ''}{profit.toFixed(2)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
