import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, CartesianGrid,
} from 'recharts';
import { Activity, Target, TrendingUp, Scale } from 'lucide-react';
import './PerformanceCharts.css';

interface Props {
  summary: Record<string, unknown>;
  daily: Record<string, unknown>[];
  grades: Record<string, unknown>;
}

interface StatCard {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
  bg: string;
}

function buildStats(
  totalTrades: number,
  winRate: number,
  totalPnl: number,
  profitFactor: number,
): StatCard[] {
  return [
    {
      icon: <Activity size={14} />,
      label: 'Total Trades',
      value: String(totalTrades),
      color: 'var(--blue)',
      bg: 'var(--blue-dim)',
    },
    {
      icon: <Target size={14} />,
      label: 'Win Rate',
      value: `${winRate}%`,
      color: winRate >= 50 ? 'var(--green)' : 'var(--red)',
      bg: winRate >= 50 ? 'var(--green-dim)' : 'var(--red-dim)',
    },
    {
      icon: <TrendingUp size={14} />,
      label: 'Total P&L',
      value: `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`,
      color: totalPnl >= 0 ? 'var(--green)' : 'var(--red)',
      bg: totalPnl >= 0 ? 'var(--green-dim)' : 'var(--red-dim)',
    },
    {
      icon: <Scale size={14} />,
      label: 'Profit Factor',
      value: profitFactor.toFixed(2),
      color: profitFactor >= 1.5 ? 'var(--green)' : profitFactor >= 1 ? 'var(--gold)' : 'var(--red)',
      bg: profitFactor >= 1.5 ? 'var(--green-dim)' : profitFactor >= 1 ? 'var(--gold-dim)' : 'var(--red-dim)',
    },
  ];
}

const tooltipStyle = {
  background: 'var(--surface)',
  border: '1px solid var(--border-hi)',
  borderRadius: 6,
  color: 'var(--text)',
  fontSize: 11,
  fontFamily: 'var(--mono)',
};

export default function PerformanceCharts({ summary, daily, grades }: Props) {
  const totalTrades = Number(summary.total_trades || 0);
  const winRate = Number(summary.win_rate || 0);
  const totalPnl = Number(summary.total_pnl || 0);
  const profitFactor = Number(summary.profit_factor || 0);

  const chartData = [...daily].reverse().map(d => ({
    date: String(d.date || '').slice(5),
    pnl: Number(d.pnl || 0),
    trades: Number(d.trades || 0),
  }));

  const gradeData = Object.entries(grades as Record<string, Record<string, unknown>>)
    .filter(([key]) => ['A+', 'B', 'SKIP'].includes(key))
    .map(([grade, data]) => ({
      grade,
      total: Number(data?.total || 0),
      executed: Number(data?.executed || 0),
    }));

  const stats = buildStats(totalTrades, winRate, totalPnl, profitFactor);

  return (
    <div className="perf-section">
      {/* Stat cards */}
      <div className="perf-grid">
        {stats.map((s, i) => (
          <div key={i} className="perf-card">
            <div className="perf-card-icon" style={{ background: s.bg, color: s.color }}>
              {s.icon}
            </div>
            <div className="perf-card-body">
              <span className="perf-card-value mono" style={{ color: s.color }}>{s.value}</span>
              <span className="perf-card-label">{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Daily P&L chart */}
      {chartData.length > 0 && (
        <div className="chart-card">
          <div className="chart-header">
            <span className="chart-title">Daily P&L</span>
            <span className="chart-sub">{chartData.length} days</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="var(--green)" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="var(--green)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(48,68,100,0.2)" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--text-2)', fontSize: 10, fontFamily: 'var(--mono)' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: 'var(--text-2)', fontSize: 10, fontFamily: 'var(--mono)' }}
                axisLine={false}
                tickLine={false}
                width={44}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                cursor={{ stroke: 'rgba(255,255,255,0.05)', strokeWidth: 1 }}
              />
              <Area
                type="monotone"
                dataKey="pnl"
                stroke="var(--green)"
                strokeWidth={1.5}
                fill="url(#pnlGrad)"
                dot={false}
                activeDot={{ r: 3, fill: 'var(--green)', strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Grade breakdown */}
      {gradeData.length > 0 && (
        <div className="chart-card">
          <div className="chart-header">
            <span className="chart-title">Decision Grades</span>
          </div>
          <ResponsiveContainer width="100%" height={140}>
            <BarChart data={gradeData} layout="vertical" margin={{ top: 0, right: 4, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="rgba(48,68,100,0.2)" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fill: 'var(--text-2)', fontSize: 10, fontFamily: 'var(--mono)' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                dataKey="grade"
                type="category"
                tick={{ fill: 'var(--text)', fontSize: 11, fontWeight: 600, fontFamily: 'var(--mono)' }}
                axisLine={false}
                tickLine={false}
                width={36}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                cursor={{ fill: 'rgba(255,255,255,0.02)' }}
              />
              <Bar dataKey="total" radius={[0, 3, 3, 0]} maxBarSize={14}>
                {gradeData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={
                      entry.grade === 'A+' ? 'var(--green)'
                      : entry.grade === 'B' ? 'var(--gold)'
                      : 'var(--text-3)'
                    }
                    fillOpacity={0.75}
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
