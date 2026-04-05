# GoldTrader AI Agent

Autonomous XAUUSD trading agent for Exness via MetaTrader 5.
Claude (primary analyst) + GPT-4o (second opinion) + risk management + Telegram notifications.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | Tested on 3.11, 3.12 |
| MetaTrader 5 | Latest | **Windows only** — MT5 Python library requires Windows |
| Exness Account | Demo or Live | XAUUSD must be available |
| API Keys | — | Anthropic, OpenAI, Perplexity |
| Telegram Bot | — | Created via [@BotFather](https://t.me/BotFather) |

> **Important:** The agent runs on Windows because MetaTrader5 Python library is Windows-only.
> Development and testing of non-MT5 components can be done on macOS/Linux.

---

## Installation

### 1. Clone and enter the project

```bash
cd /path/to/trading_agent
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # macOS/Linux (for non-MT5 dev)
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
copy .env.example .env   # Windows
# or: cp .env.example .env  # macOS/Linux
```

Edit `.env` with your actual values:

```dotenv
# Required — agent will not start without these
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=-100...

# MT5 Demo (required)
MT5_DEMO_LOGIN=12345678
MT5_DEMO_PASSWORD=your_password
MT5_DEMO_SERVER=Exness-MT5Trial9

# MT5 Live (fill when ready)
MT5_LIVE_LOGIN=
MT5_LIVE_PASSWORD=
MT5_LIVE_SERVER=

# Start with demo
ACTIVE_ACCOUNT=demo
```

### 5. Verify MT5 connection

Open MetaTrader 5, log into your Exness account, and ensure XAUUSD is visible in Market Watch.

---

## Quick Start (Windows Batch Files)

Double-click these on your Windows machine — no terminal needed:

| File | What it does |
|---|---|
| `setup.bat` | First time: creates venv, installs deps, copies .env template |
| `start_dry.bat` | Dry run with debug logging — no trades, full pipeline |
| `start_demo.bat` | Demo execution — checks .env is set to demo first |
| `start_live.bat` | Live execution — red console, requires typing "LIVE" to confirm |
| `logs.bat` | Interactive log viewer (tail, filter trades/errors/decisions) |

**First time workflow:**
```
1. Double-click setup.bat
2. Edit .env with your credentials
3. Open MetaTrader 5
4. Double-click start_dry.bat
```

---

## Running the Agent (Manual)

### Dry Run (recommended first)

Runs the full pipeline without placing trades. Logs all decisions.

```bash
python -m agent.main --dry-run
```

### Dry Run with Debug Logging

Shows all indicator values, context packages, and API responses.

```bash
python -m agent.main --dry-run --debug
```

### Live Execution (Demo)

Executes trades on your demo account. Ensure `ACTIVE_ACCOUNT=demo` in `.env`.

```bash
python -m agent.main
```

### Live Execution (Real Money)

**Only after demo validation.** Set `ACTIVE_ACCOUNT=live` in `.env` and fill live credentials.

```bash
# Edit .env first:
# ACTIVE_ACCOUNT=live
# MT5_LIVE_LOGIN=...
# MT5_LIVE_PASSWORD=...
# MT5_LIVE_SERVER=...

python -m agent.main
```

### Stopping the Agent

Press `Ctrl+C`. The agent will:
1. Finish the current cycle
2. Update database state to "shutdown"
3. Send Telegram notification
4. Disconnect from MT5

**Open positions are NOT closed on shutdown.** They remain managed by MT5's SL/TP.

---

## Risk Configuration

All risk parameters are in `.env` with safe defaults:

| Parameter | Default | Description |
|---|---|---|
| `MAX_RISK_PER_TRADE` | `0.02` (2%) | Risk per trade as fraction of balance |
| `MAX_DAILY_LOSS_USD` | `50` | Daily loss limit — stops trading when hit |
| `MAX_POSITIONS` | `2` | Maximum simultaneous open positions |
| `SL_MIN_POINTS` | `8` | Minimum stop loss distance (1 point = $0.01) |
| `SL_MAX_POINTS` | `50` | Maximum stop loss distance |
| `MIN_RR_RATIO` | `1.5` | Minimum reward-to-risk ratio |
| `POST_TRADE_COOLING_MINUTES` | `20` | Cooldown after any trade |
| `POST_LOSS_COOLING_MINUTES` | `30` | Cooldown after a losing trade |

> **Scaling risk:** Start with 2% during demo. After consistent demo profitability,
> increase to `0.05` (5%) for live structured scalping with tight stops.

---

## Trading Windows (GMT+0)

The agent only operates during two windows. Outside these, it sleeps with zero API calls.

| Window | Time (GMT+0) | Session |
|---|---|---|
| Window 1 | 23:00 – 01:00 | Asia Open |
| Window 2 | 12:00 – 14:00 | London-NY Overlap |

Configure in `.env`:
```dotenv
WINDOW_1_START=23:00
WINDOW_1_END=01:00
WINDOW_2_START=12:00
WINDOW_2_END=14:00
```

---

## Checking Logs

Logs are stored in `agent/logs/` with daily rotation (30-day retention).

```bash
# Live tail
tail -f agent/logs/agent.log

# Search for trades
grep "PLACED\|CLOSED\|TP1 HIT" agent/logs/agent.log

# Search for errors
grep "ERROR\|CRITICAL" agent/logs/agent.log

# View Claude decisions
grep "Claude:" agent/logs/agent.log
```

### Log Format
```
2026-04-05 23:15:02 | INFO | main | WINDOW: Asia Open (23:00-01:00) | 15min in | session=ASIA
2026-04-05 23:15:02 | INFO | main | Prefilter PASS — proceeding to news check
2026-04-05 23:15:03 | INFO | claude_agent | A+ | direction=BUY, confidence=82
2026-04-05 23:15:04 | INFO | gpt_agent | CONFIRM | Setup looks solid
2026-04-05 23:15:04 | INFO | risk | PASS | direction=BUY, sl_points=15, lot_size=0.05
2026-04-05 23:15:05 | INFO | executor | PLACED | ticket=12345, BUY 0.05 lots @ 2365.50
```

---

## Telegram Alerts

The agent sends 7 types of notifications:

| Alert | Emoji | Trigger |
|---|---|---|
| Trade Placed | 🟢 | A+ setup executed |
| Setup Alert | 🟡 | B grade — manual execution only |
| GPT Challenge | 🔶 | A+ downgraded to B by GPT |
| Risk Blocked | 🔴 | A+ passed GPT but failed risk checks |
| News Alert | ⚠️ | High-impact event — setup skipped |
| Skip | ⚪ | No tradeable setup found |
| Agent Status | 🤖 | Startup / Shutdown |

---

## Architecture

```
MT5 (M15 close) → prefilter (free) → news check → context builder
    → Claude (primary) → GPT (A+ only) → risk validation → executor
    → database + Telegram
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full technical details.  
See [PLAYBOOK.md](PLAYBOOK.md) for trading strategy and Claude system prompt.  
See [TASKS.md](TASKS.md) for build status.

---

## Project Structure

```
trading_agent/
├── agent/                 # Core agent (Phase 1)
│   ├── main.py           # Entry point, orchestration loop
│   ├── config.py         # .env loading, validation
│   ├── database.py       # SQLite persistence
│   ├── windows.py        # Trading window detection
│   ├── market.py         # MT5 data fetching
│   ├── indicators.py     # Technical analysis (EMA, RSI, MACD, ATR)
│   ├── prefilter.py      # Zero-cost local signal gate
│   ├── news.py           # MT5 calendar + Perplexity fallback
│   ├── context.py        # Claude context package builder
│   ├── claude_agent.py   # Claude API with prompt caching
│   ├── gpt_agent.py      # GPT-4o second opinion
│   ├── risk.py           # Pre-execution risk validation
│   ├── executor.py       # MT5 order placement + TP1 monitor
│   ├── notifier.py       # Telegram notifications
│   ├── data/             # SQLite database (gitignored)
│   └── logs/             # Daily rotating logs (gitignored)
├── api/                   # FastAPI gateway (Phase 2)
├── dashboard/             # React/Vite dashboard (Phase 3)
├── AGENT.md              # System identity document
├── ARCHITECTURE.md       # Technical blueprint
├── PLAYBOOK.md           # Trading strategy / Claude system prompt
├── TASKS.md              # Build task queue
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
└── .gitignore
```

---

## Key Identifiers

| Identifier | Value | Purpose |
|---|---|---|
| Magic Number | `234001` | Distinguishes agent trades from mt5-bot (`234000`) |
| Points | 1 point = $0.01 | XAUUSD price units (not pips) |
| Lot Size | Formula | `balance × risk% / sl_points` |

---

## Troubleshooting

### "FATAL: Missing required environment variable"
Copy `.env.example` to `.env` and fill in all required values.

### "MT5 initialize failed"
- Ensure MetaTrader 5 is running and logged in
- Check that the MT5 Python library is installed: `pip install MetaTrader5`
- Only works on Windows

### "Claude API unavailable after 3 attempts"
- Check your `ANTHROPIC_API_KEY` is valid
- Check API rate limits at [console.anthropic.com](https://console.anthropic.com)
- Agent will SKIP (not crash) and retry next cycle

### Agent not trading during windows
- Check your system clock is correct (agent uses UTC)
- Run with `--debug` to see prefilter decisions
- Check `agent/logs/agent.log` for FAIL reasons

### No Telegram messages
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Send `/start` to your bot first
- Agent logs Telegram failures but never crashes
