import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import './PerformanceCharts.css';

interface Props {
  summary: Record<string, unknown>;
  daily: Record<string, unknown>[];
  grades: Record<string, unknown>;
}

export default function PerformanceCharts({ summary, daily, grades }: Props) {
  const totalTrades = Number(summary.total_trades || 0);
  const winRate = Number(summary.win_rate || 0);
  const totalPnl = Number(summary.total_pnl || 0);
  const profitFactor = Number(summary.profit_factor || 0);

  // Prepare daily chart data
  const chartData = [...daily].reverse().map(d => ({
    date: String(d.date || '').slice(5),
    pnl: Number(d.pnl || 0),
    trades: Number(d.trades || 0),
  }));

  // Grade breakdown
  const gradeData = Object.entries(grades as Record<string, Record<string, unknown>>)
    .filter(([key]) => ['A+', 'B', 'SKIP'].includes(key))
    .map(([grade, data]) => ({
      grade,
      total: Number(data?.total || 0),
      executed: Number(data?.executed || 0),
    }));

  return (
    <div className="performance-section">
      {/* Stat Cards */}
      <div className="perf-stats">
        <div className="perf-stat">
          <span className="perf-stat-value">{totalTrades}</span>
          <span className="perf-stat-label">Total Trades</span>
        </div>
        <div className="perf-stat">
          <span className="perf-stat-value" style={{ color: winRate >= 50 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {winRate}%
          </span>
          <span className="perf-stat-label">Win Rate</span>
        </div>
        <div className="perf-stat">
          <span className={`perf-stat-value ${totalPnl >= 0 ? 'positive' : 'negative'}`}>
            ${totalPnl.toFixed(2)}
          </span>
          <span className="perf-stat-label">Total P&L</span>
        </div>
        <div className="perf-stat">
          <span className="perf-stat-value">{profitFactor.toFixed(2)}</span>
          <span className="perf-stat-label">Profit Factor</span>
        </div>
      </div>

      {/* Daily P&L Chart */}
      {chartData.length > 0 && (
        <div className="chart-card">
          <h3>Daily P&L</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-green)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--accent-green)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: 'var(--card-bg)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  color: 'var(--text-primary)',
                }}
              />
              <Area type="monotone" dataKey="pnl" stroke="var(--accent-green)" fill="url(#pnlGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Grade Breakdown */}
      {gradeData.length > 0 && (
        <div className="chart-card">
          <h3>Grade Breakdown</h3>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={gradeData} layout="vertical">
              <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis dataKey="grade" type="category" tick={{ fill: 'var(--text-primary)', fontSize: 12, fontWeight: 600 }} width={40} />
              <Tooltip
                contentStyle={{
                  background: 'var(--card-bg)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  color: 'var(--text-primary)',
                }}
              />
              <Bar dataKey="total" radius={[0, 6, 6, 0]}>
                {gradeData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      entry.grade === 'A+'
                        ? 'var(--accent-green)'
                        : entry.grade === 'B'
                        ? 'var(--accent-gold)'
                        : 'var(--text-muted)'
                    }
                    fillOpacity={0.6}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
