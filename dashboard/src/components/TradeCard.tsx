import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import './TradeCard.css';

interface Props {
  trades: Record<string, unknown>[];
}

export default function TradeCard({ trades }: Props) {
  return (
    <div className="trade-card">
      <div className="card-header">
        <span className="card-title">Recent Trades</span>
        <span className="card-count">{trades.length}</span>
      </div>

      {!trades.length ? (
        <div className="empty-state">
          <Minus size={20} strokeWidth={1.5} />
          <span>No trades yet</span>
        </div>
      ) : (
        <div className="trades-list">
          {trades.slice(0, 10).map((trade, i) => {
            const dir = String(trade.direction || '').toUpperCase();
            const profit = Number(trade.profit_usd || 0);
            const entry = Number(trade.entry_price || 0);
            const lots = Number(trade.lot_size || 0);
            const sl = Number(trade.sl_level || 0);
            const tp1 = Number(trade.tp1_level || 0);
            const time = trade.timestamp_open
              ? new Date(String(trade.timestamp_open)).toLocaleString([], {
                  month: 'short', day: 'numeric',
                  hour: '2-digit', minute: '2-digit',
                })
              : '—';
            const status = String(trade.status || 'open');
            const isBuy = dir === 'BUY';

            return (
              <div key={i} className="trade-row">
                <div className={`dir-icon ${isBuy ? 'buy' : 'sell'}`}>
                  {isBuy
                    ? <ArrowUpRight size={14} />
                    : <ArrowDownRight size={14} />}
                </div>

                <div className="trade-main">
                  <div className="trade-top-row">
                    <span className={`dir-badge ${isBuy ? 'buy' : 'sell'}`}>{dir}</span>
                    <span className="trade-lots">{lots} lots</span>
                    <span className={`trade-status status-${status}`}>{status}</span>
                  </div>
                  <div className="trade-bot-row">
                    <span className="trade-price mono">Entry {entry.toFixed(2)}</span>
                    {sl > 0 && <span className="trade-level">SL {sl.toFixed(2)}</span>}
                    {tp1 > 0 && <span className="trade-level">TP {tp1.toFixed(2)}</span>}
                    <span className="trade-time">{time}</span>
                  </div>
                </div>

                <div className={`trade-pnl ${profit > 0 ? 'win' : profit < 0 ? 'loss' : 'flat'}`}>
                  {profit > 0 ? '+' : ''}{profit !== 0 ? profit.toFixed(2) : '—'}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
