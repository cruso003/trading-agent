import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Navbar from '../components/Navbar';
import './Landing.css';

const API_BASE = 'http://localhost:8000/api';

interface Summary {
  win_rate?: number;
  total_trades?: number;
  total_pnl?: number;
  profit_factor?: number;
  agent_status?: string;
}

interface DailyPoint {
  date: string;
  pnl: number;
  cumulative_pnl?: number;
}

function formatPct(v: number | undefined): string {
  if (v === undefined || v === null) return '—';
  return `${v.toFixed(1)}%`;
}

function formatPnl(v: number | undefined): string {
  if (v === undefined || v === null) return '—';
  const sign = v >= 0 ? '+' : '';
  return `${sign}$${v.toFixed(2)}`;
}

function formatNumber(v: number | undefined): string {
  if (v === undefined || v === null) return '—';
  return String(v);
}

function formatFactor(v: number | undefined): string {
  if (v === undefined || v === null) return '—';
  return v.toFixed(2);
}

interface TooltipPayload {
  value: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const val = payload[0].value;
  const sign = val >= 0 ? '+' : '';
  return (
    <div className="landing-chart-tooltip">
      <div className="landing-chart-tooltip-date">{label}</div>
      <div className={`landing-chart-tooltip-val ${val >= 0 ? 'pos' : 'neg'}`}>
        {sign}${val.toFixed(2)}
      </div>
    </div>
  );
}

export default function Landing() {
  const [summary, setSummary] = useState<Summary>({});
  const [daily, setDaily] = useState<DailyPoint[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API_BASE}/analytics/summary`);
        if (res.ok) {
          const data = await res.json() as Summary;
          setSummary(data);
        }
      } catch { /* silent */ }
      try {
        const res = await fetch(`${API_BASE}/analytics/daily`);
        if (res.ok) {
          const data = await res.json() as DailyPoint[];
          setDaily(data);
        }
      } catch { /* silent */ }
    }
    load();
  }, []);

  const agentStatusLabel = (() => {
    const s = summary.agent_status || '';
    if (s === 'watching') return 'Watching';
    if (s === 'analysing') return 'Analysing';
    if (s === 'executing') return 'Executing';
    if (s === 'sleeping') return 'Sleeping';
    if (!s) return '—';
    return s.charAt(0).toUpperCase() + s.slice(1);
  })();

  return (
    <div className="landing">
      <Navbar />

      {/* HERO */}
      <section className="landing-hero">
        <div className="landing-hero-glow" />
        <div className="landing-container">
          <div className="landing-hero-inner">
            <div className="landing-label">AI-POWERED GOLD TRADING</div>
            <h1 className="landing-hero-headline">
              The machine trades.<br />
              You learn why.
            </h1>
            <p className="landing-hero-sub">
              ApexGold is an AI system that trades XAUUSD around the clock. Every decision is logged,
              every trade is public. Join the mentorship program and trade alongside it.
            </p>
            <div className="landing-hero-ctas">
              <Link to="/apply" className="landing-cta-primary">Apply for Access</Link>
              <button
                className="landing-cta-ghost"
                onClick={() => {
                  const el = document.getElementById('performance');
                  if (el) el.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                View Performance
              </button>
            </div>
            <div className="landing-hero-stats">
              <div className="landing-hero-stat">
                <span className="landing-hero-stat-val">{formatPct(summary.win_rate)}</span>
                <span className="landing-hero-stat-label">Win Rate</span>
              </div>
              <div className="landing-hero-stat-divider" />
              <div className="landing-hero-stat">
                <span className="landing-hero-stat-val">{formatNumber(summary.total_trades)}</span>
                <span className="landing-hero-stat-label">Total Trades</span>
              </div>
              <div className="landing-hero-stat-divider" />
              <div className="landing-hero-stat">
                <span className="landing-hero-stat-val">{agentStatusLabel}</span>
                <span className="landing-hero-stat-label">Agent Status</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PERFORMANCE */}
      <section className="landing-section landing-section-alt" id="performance">
        <div className="landing-container">
          <div className="landing-label">TRACK RECORD</div>
          <h2 className="landing-section-headline">Every trade. Public. Verified.</h2>
          <p className="landing-section-sub">
            The agent has been running live since launch. Nothing is hidden.
          </p>

          <div className="landing-stat-cards">
            <div className="landing-stat-card">
              <span className="landing-stat-card-val">{formatPct(summary.win_rate)}</span>
              <span className="landing-stat-card-label">Win Rate</span>
            </div>
            <div className="landing-stat-card">
              <span className="landing-stat-card-val">{formatNumber(summary.total_trades)}</span>
              <span className="landing-stat-card-label">Total Trades</span>
            </div>
            <div className="landing-stat-card">
              <span className={`landing-stat-card-val ${(summary.total_pnl ?? 0) >= 0 ? 'pos' : 'neg'}`}>
                {formatPnl(summary.total_pnl)}
              </span>
              <span className="landing-stat-card-label">Total P&L</span>
            </div>
            <div className="landing-stat-card">
              <span className="landing-stat-card-val">{formatFactor(summary.profit_factor)}</span>
              <span className="landing-stat-card-label">Profit Factor</span>
            </div>
          </div>

          {daily.length > 0 && (
            <div className="landing-chart-wrap">
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={daily} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--gold)" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="var(--gold)" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="date"
                    tick={{ fill: 'var(--text-2)', fontSize: 10, fontFamily: 'var(--mono)' }}
                    axisLine={false}
                    tickLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fill: 'var(--text-2)', fontSize: 10, fontFamily: 'var(--mono)' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => `$${v}`}
                    width={52}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="pnl"
                    stroke="var(--gold)"
                    strokeWidth={1.5}
                    fill="url(#pnlGradient)"
                    dot={false}
                    activeDot={{ r: 4, fill: 'var(--gold)', stroke: 'var(--bg)', strokeWidth: 2 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          <p className="landing-disclaimer">
            Past performance does not guarantee future results. Trading involves risk.
          </p>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="landing-section" id="how-it-works">
        <div className="landing-container">
          <div className="landing-label">THE SYSTEM</div>
          <h2 className="landing-section-headline">How it works</h2>

          <div className="landing-steps">
            <div className="landing-step">
              <div className="landing-step-num">01</div>
              <h3 className="landing-step-title">AI Analyzes the Market</h3>
              <p className="landing-step-desc">
                Claude AI analyzes XAUUSD every 15 minutes during key trading windows,
                reading price structure, momentum, and market context.
              </p>
            </div>
            <div className="landing-step-connector" />
            <div className="landing-step">
              <div className="landing-step-num">02</div>
              <h3 className="landing-step-title">High-Probability Setups</h3>
              <p className="landing-step-desc">
                Only A+ and B grade setups pass 5 pre-trade filters before execution.
                The majority of analysis results in a deliberate pass.
              </p>
            </div>
            <div className="landing-step-connector" />
            <div className="landing-step">
              <div className="landing-step-num">03</div>
              <h3 className="landing-step-title">You Trade Alongside It</h3>
              <p className="landing-step-desc">
                You receive signals, see the reasoning, and learn the same patterns
                the AI uses to identify and execute trades.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* WHAT YOU GET */}
      <section className="landing-section landing-section-alt" id="mentorship">
        <div className="landing-container">
          <div className="landing-label">MENTORSHIP</div>
          <h2 className="landing-section-headline">Not just signals. Understanding.</h2>
          <p className="landing-section-sub">
            The goal isn't dependency. It's competence.
          </p>

          <div className="landing-benefits">
            <div className="landing-benefit-card">
              <div className="landing-benefit-icon">
                <span className="landing-benefit-dot" />
              </div>
              <h3 className="landing-benefit-title">Live Signal Feed</h3>
              <p className="landing-benefit-desc">
                Every trade the AI executes, explained in plain English with entry,
                stop loss, and target. No black box.
              </p>
            </div>
            <div className="landing-benefit-card">
              <div className="landing-benefit-icon">
                <span className="landing-benefit-dot" />
              </div>
              <h3 className="landing-benefit-title">Session Analysis</h3>
              <p className="landing-benefit-desc">
                After each trading session, see what the AI saw and why it acted
                or waited. Every skip is documented.
              </p>
            </div>
            <div className="landing-benefit-card">
              <div className="landing-benefit-icon">
                <span className="landing-benefit-dot" />
              </div>
              <h3 className="landing-benefit-title">Academy Access</h3>
              <p className="landing-benefit-desc">
                Structured curriculum covering the gold market, risk management,
                and trading psychology built on real-world application.
              </p>
            </div>
            <div className="landing-benefit-card">
              <div className="landing-benefit-icon">
                <span className="landing-benefit-dot" />
              </div>
              <h3 className="landing-benefit-title">Direct Mentorship</h3>
              <p className="landing-benefit-desc">
                Work directly with the mentor. Limited spots. Not an automated
                course. Application required.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ACADEMY PREVIEW */}
      <section className="landing-section" id="academy">
        <div className="landing-container">
          <div className="landing-label">ACADEMY</div>
          <h2 className="landing-section-headline">Learn the framework.</h2>
          <p className="landing-section-sub">
            Four modules. From understanding gold to trading psychology.
            Everything the AI was built on.
          </p>
          <div className="landing-academy-modules">
            <div className="landing-module landing-module-available">
              <span className="landing-module-num">01</span>
              <span className="landing-module-name">Understanding the Gold Market</span>
              <span className="landing-module-badge badge-available">Available</span>
            </div>
            <div className="landing-module">
              <span className="landing-module-num">02</span>
              <span className="landing-module-name">How the AI Reads Setups</span>
              <span className="landing-module-badge badge-soon">Coming Soon</span>
            </div>
            <div className="landing-module">
              <span className="landing-module-num">03</span>
              <span className="landing-module-name">Risk Management</span>
              <span className="landing-module-badge badge-soon">Coming Soon</span>
            </div>
            <div className="landing-module">
              <span className="landing-module-num">04</span>
              <span className="landing-module-name">Trading Psychology</span>
              <span className="landing-module-badge badge-soon">Coming Soon</span>
            </div>
          </div>
        </div>
      </section>

      {/* APPLY CTA */}
      <section className="landing-section landing-section-cta" id="apply">
        <div className="landing-container landing-container-center">
          <h2 className="landing-cta-headline">Applications are reviewed manually.</h2>
          <p className="landing-cta-sub">
            Not everyone gets in. We work with serious people who want to understand
            trading, not just copy signals.
          </p>
          <Link to="/apply" className="landing-cta-primary landing-cta-large">
            Submit Your Application
          </Link>
          <p className="landing-cta-note">Free to apply. No commitment required.</p>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="landing-footer">
        <div className="landing-container landing-footer-inner">
          <div className="landing-footer-brand">
            <span className="landing-footer-apex">APEX</span>
            <span className="landing-footer-gold">GOLD</span>
          </div>
          <p className="landing-footer-center">
            Built on live AI trading. For educational purposes.
          </p>
          <p className="landing-footer-year">{new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}
