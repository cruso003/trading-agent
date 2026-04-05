# GoldTrader AI Agent — Technical Architecture

# This is the technical blueprint for the entire system.

# Every Claude Code session must read this before writing code.

---

## 1. System Overview (Three-Layer Architecture)

The system is divided into three distinct layers:

- Layer 1: Agent Core (Python)
  The brain. Handles MT5 connectivity, technical analysis,
  LLM orchestration, and trade execution.
  Operates on a 24/7 loop triggered by M15 candle closes.

- Layer 2: API Gateway (FastAPI)
  Exposes internal agent state and trade history via REST.
  Broadcasts real-time events to dashboard using SSE.

- Layer 3: Trading Dashboard (Vite + React)
  Real-time interface for monitoring agent analysis,
  performance metrics, and remote controls.

---

## 2. Intelligence & LLM Architecture

### Multi-Agent Pipeline

| Agent           | Role                  | Model             | Trigger        |
| --------------- | --------------------- | ----------------- | -------------- |
| Primary Analyst | Main Setup Evaluation | claude-sonnet-4-6 | Prefilter Pass |
| Second Opinion  | A+ Setup Verification | gpt-4o            | Claude = A+    |
| News Analyst    | Macro Risk Guard      | Perplexity        | ATR Spike Only |

### Daily Cost Estimate

- Claude: 4-6 calls × ~$0.004 = ~$0.02/day
  (system prompt cached, ~90% reduction via cache_control)
- GPT-4o: 1-2 calls × ~$0.008 = ~$0.01/day
- Perplexity: $0.00 normal / ~$0.002 anomalous days
- Total: ~$0.03/day (~$0.90/month)

### Intelligence Design Principles

AI Isolation Principle:

- Claude and GPT are account-blind
- They receive balance and risk data but never know
  if they are on Demo or Live account
- Ensures identical seriousness across environments
- Account type known only to: config.py, executor.py,
  database.py, notifier.py

Prompt Caching:

- PLAYBOOK.md system prompt uses cache_control: ephemeral
- Reduces Claude API cost ~90% on repeated calls within day
- Only context package (user message) billed fresh each call

GPT Independence:

- GPT-4o receives raw market context + Claude analysis
- GPT does NOT see Claude reasoning before forming own view
- Ensures unbiased second opinion, not rubber-stamping
- If GPT challenges: downgrade to B, Telegram alert, no execution

Perplexity Caching:

- Result cached 15 minutes per window
- Avoids redundant calls for same market condition

Demo/Live Rule:

- Demo and Live never run simultaneously
- Switch is config-level only (ACTIVE_ACCOUNT in .env)
- Zero changes to AI layer when switching environments

---

## 3. Trading Pipeline (Process View)

```
MT5: M15 Candle Close
        ↓
market.py: Fetch OHLCV + account data
        ↓
indicators.py: Calculate EMA/RSI/ATR/MACD/body ratios
        ↓
windows.py: Check GMT+0 trading windows
  Window 1: 23:00-01:00
  Window 2: 12:00-14:00
  Outside? Sleep 60s, repeat
        ↓
prefilter.py: Zero-cost logic gate
  Checks:
  - H4 and H1 direction agree
  - M30 body strength not in dead zone (40-55%)
  - Not in post-trade cooling period
  - Price not mid-range (position 35-65%)
  - No position already open in same direction
  Fails? Log reason, sleep until next M15, repeat
        ↓
news.py: News and macro risk check
  Step 1: MT5 Economic Calendar
    HIGH impact event within 60 minutes?
    YES → Skip + Telegram alert, sleep
  Step 2: ATR anomaly check
    ATR > 2x 20-period average?
    YES → Call Perplexity for context
    Perplexity returns HIGH? → Skip + Telegram
  Passes both? Continue
        ↓
context.py: Build full context package
  - All indicator values
  - Last 5 M30 candle sequence
  - Session high/low and price position
  - Last 5 agent decisions with outcomes
  - Last 3 trade results
  - Account balance (number only, no label)
  - Minutes into current window
  - News context
        ↓
claude_agent.py: Primary analysis
  - System prompt: PLAYBOOK.md (cached)
  - User message: full context package
  - Returns strict JSON decision
  SKIP? Log + Telegram skip notification, continue loop
  B? Log + Telegram B alert with full parameters, continue
  A+? Continue to GPT second opinion
        ↓
gpt_agent.py: Independent second opinion (A+ only)
  - Receives market context + Claude analysis
  - Forms independent view without seeing Claude reasoning
  CHALLENGE? Downgrade to B, log + Telegram, continue loop
  CONFIRM? Continue to risk check
        ↓
risk.py: Pre-execution validation
  Checks:
  - Daily loss limit not exceeded
  - Max positions not reached (max 2)
  - SL distance between 8-50 points
  - Account balance above minimum threshold
  - Lot size calculated (2% rule)
  Fails? Log + Telegram blocked alert, continue loop
        ↓
executor.py: Place trade on MT5
  - Connects to correct account (from config)
  - Places market order with SL, TP1, TP2
  - Magic number: 234001
  - Verifies placement by checking positions
  - Records ticket ID
        ↓
database.py: Log full decision record
        ↓
notifier.py: Telegram execution confirmation
        ↓
Sleep until next M15 candle close, repeat
```

---

## 4. Data Architecture

### SQLite Schema (agent.db)

```sql
-- Every agent decision regardless of outcome
CREATE TABLE agent_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    window_name TEXT,
    grade TEXT,
    direction TEXT,
    entry_price REAL,
    entry_zone TEXT,
    sl_level REAL,
    tp1_level REAL,
    tp2_level REAL,
    invalidation TEXT,
    reasoning TEXT,
    confidence INTEGER,
    pillar_trend TEXT,
    pillar_momentum TEXT,
    pillar_location TEXT,
    setup_type TEXT,
    base_zone TEXT,
    news_risk TEXT,
    news_summary TEXT,
    gpt_verdict TEXT,
    gpt_reasoning TEXT,
    executed BOOLEAN DEFAULT FALSE,
    skip_reason TEXT,
    execution_reason TEXT
);

-- Every trade placed by agent
CREATE TABLE agent_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER UNIQUE,
    timestamp_open TEXT,
    timestamp_close TEXT,
    direction TEXT,
    lot_size REAL,
    entry_price REAL,
    sl_price REAL,
    tp1_price REAL,
    tp2_price REAL,
    exit_price REAL,
    profit_usd REAL,
    profit_pips REAL,
    exit_reason TEXT,
    account_type TEXT,
    decision_id INTEGER,
    FOREIGN KEY (decision_id) REFERENCES agent_decisions(id)
);

-- Performance aggregated by window
CREATE TABLE window_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    window_name TEXT,
    trades_taken INTEGER DEFAULT 0,
    trades_won INTEGER DEFAULT 0,
    trades_lost INTEGER DEFAULT 0,
    total_pnl REAL DEFAULT 0,
    avg_confidence REAL,
    claude_a_plus INTEGER DEFAULT 0,
    gpt_challenges INTEGER DEFAULT 0,
    UNIQUE(date, window_name)
);

-- Agent state for dashboard
CREATE TABLE agent_state (
    id INTEGER PRIMARY KEY,
    status TEXT,
    current_window TEXT,
    last_analysis_time TEXT,
    last_trade_time TEXT,
    daily_pnl REAL,
    updated_at TEXT
);
```

### Magic Numbers

- Agent Magic Number: 234001
- mt5-bot Magic Number: 234000
- Never use 234000 in agent code

---

## 5. SSE Event Types

```
agent_status      — sleeping/watching/analysing/executing
window_open       — trading window started
window_closed     — trading window ended
prefilter_pass    — prefilter passed, APIs being called
prefilter_fail    — prefilter failed with reason
news_alert        — HIGH risk news detected, skipping
analysis_done     — Claude returned grade and reasoning
gpt_confirm       — GPT confirmed A+ setup
gpt_challenge     — GPT challenged, downgraded to B
trade_placed      — execution confirmed with full details
trade_closed      — position closed with outcome
tp1_hit           — first take profit level reached
risk_blocked      — A+ blocked by risk rules
b_alert           — B grade setup, manual alert sent
skip_logged       — SKIP with reason
```

---

## 6. REST API Endpoints (Phase 2)

```
GET  /api/status                  — agent current state
GET  /api/trades                  — trade history with filters
GET  /api/trades/:id              — single trade detail
GET  /api/decisions               — full decision log
GET  /api/analytics/summary       — overall performance metrics
GET  /api/analytics/windows       — performance by window
GET  /api/analytics/daily         — daily P&L history
GET  /api/analytics/grades        — A+/B/SKIP breakdown
POST /api/control/demo            — switch to demo mode
POST /api/control/live            — switch to live mode
POST /api/control/pause           — pause agent
POST /api/control/resume          — resume agent
POST /api/control/window1/toggle  — enable/disable window 1
POST /api/control/window2/toggle  — enable/disable window 2
GET  /api/stream                  — SSE endpoint
```

---

## 7. Telegram Notification Templates

### A+ Executed

```
🟢 TRADE PLACED
XAUUSD {direction} | {lot_size} lots
Entry: {entry_price}
TP1: {tp1_level}
TP2: {tp2_level}
SL: {sl_level}
Window: {window_name}
Confidence: {confidence}%
Reason: {reasoning}
[{account_type}]
```

### B Alert — Full Parameters for Manual Entry

```
🟡 SETUP ALERT — Grade B

{direction} XAUUSD @ {entry_price}
TP1: {tp1_level}
TP2: {tp2_level}
SL:  {sl_level}

Window: {window_name}
Invalidation: {invalidation}
Reason: {reasoning}

Manual execution only
```

### GPT Challenge (downgraded from A+)

```
🔶 SETUP DOWNGRADED — A+ → B
Claude: A+ | GPT: CHALLENGE

{direction} XAUUSD @ {entry_price}
TP1: {tp1_level}
TP2: {tp2_level}
SL:  {sl_level}

GPT concern: {gpt_reasoning}
Manual execution only
```

### Risk Blocked

```
🔴 TRADE BLOCKED
Grade: A+ | GPT: CONFIRMED
Blocked by: {risk_reason}

Setup preserved in log ID: {decision_id}
```

### News Alert

```
⚠️ NEWS ALERT — SETUP SKIPPED
Risk: HIGH
{news_summary}

Next check at next M15 close
```

### Skip

```
⚪ SKIPPED
{skip_reason}
```

### TP1 Hit (position management)

```
💰 TP1 HIT
XAUUSD {direction} | Ticket: {ticket_id}
TP1: {tp1_level} reached
SL moved to breakeven: {entry_price}
Runner targeting TP2: {tp2_level}
[{account_type}]
```

---

## 8. Operational Constraints

### Trading Windows (GMT+0)

- Window 1 (Asia Open): 23:00 – 01:00
- Window 2 (London-NY Overlap): 12:00 – 14:00
- Outside windows: zero API calls, agent sleeps

### Cooling Periods

- After any trade closes: 20 minutes minimum
- After a losing trade: 30 minutes minimum
- During cooling: prefilter blocks all setups

### Risk Rules

- Max risk per trade: 2% of account balance
- Max simultaneous positions: 2
- Daily loss limit: MAX_DAILY_LOSS_USD from .env
- SL minimum distance: 8 points
- SL maximum distance: 50 points
- If daily loss limit hit: agent disables for the day

### TP Management

- TP1 hit: close 50% of position
- Move SL to breakeven (entry price)
- Let remaining 50% run to TP2
- This is handled by executor.py monitoring open positions

---

## 9. Environment Variables (.env)

```bash
# AI APIs
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
PERPLEXITY_API_KEY=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# MT5 Demo
MT5_DEMO_LOGIN=
MT5_DEMO_PASSWORD=
MT5_DEMO_SERVER=

# MT5 Live
MT5_LIVE_LOGIN=
MT5_LIVE_PASSWORD=
MT5_LIVE_SERVER=

# Active Account (demo or live — never both)
ACTIVE_ACCOUNT=demo

# Risk Parameters
MAX_DAILY_LOSS_USD=50
MAX_POSITIONS=2
MAX_RISK_PER_TRADE=0.02
SL_MIN_POINTS=8
SL_MAX_POINTS=50
MIN_RR_RATIO=1.5
POST_TRADE_COOLING_MINUTES=20
POST_LOSS_COOLING_MINUTES=30

# Trading Windows (GMT+0)
WINDOW_1_START=23:00
WINDOW_1_END=01:00
WINDOW_2_START=12:00
WINDOW_2_END=14:00

# Models
CLAUDE_MODEL=claude-sonnet-4-6
GPT_MODEL=gpt-4o

# Runtime
LOG_LEVEL=INFO
DB_PATH=agent/data/agent.db
NEWS_CACHE_MINUTES=15
```

---

## 10. Directory Structure

```
trading_agent/
├── AGENT.md              # master system document
├── ARCHITECTURE.md       # this file
├── PLAYBOOK.md           # trading strategy + Claude system prompt
├── TASKS.md              # build status and task queue
├── .env                  # credentials (never commit)
├── requirements.txt      # Python dependencies
│
├── agent/                # Phase 1: Agent core
│   ├── main.py           # entry point + main loop
│   ├── config.py         # loads .env, all settings
│   ├── windows.py        # trading window detection GMT+0
│   ├── market.py         # MT5 connection + data fetch
│   ├── indicators.py     # calculates H4/H1/M30/M15
│   ├── context.py        # builds full context package
│   ├── prefilter.py      # local signal filter, zero API cost
│   ├── news.py           # MT5 calendar + Perplexity fallback
│   ├── claude_agent.py   # Claude primary analysis
│   ├── gpt_agent.py      # GPT-4o second opinion (A+ only)
│   ├── risk.py           # risk validation before execution
│   ├── executor.py       # MT5 trade execution + TP management
│   ├── notifier.py       # Telegram notifications
│   ├── database.py       # SQLite logging
│   └── data/
│       └── agent.db      # SQLite database
│
├── api/                  # Phase 2: FastAPI layer
│   ├── main.py           # FastAPI app entry point
│   ├── state.py          # shared state between agent + API
│   └── routes/
│       ├── agent.py      # status + control endpoints
│       ├── trades.py     # trade history endpoints
│       ├── analytics.py  # performance metrics endpoints
│       └── stream.py     # SSE endpoint
│
├── dashboard/            # Phase 3: Vite + React
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentStatus.tsx
│   │   │   ├── TradeCard.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── AnalysisPanel.tsx
│   │   │   ├── PerformanceCharts.tsx
│   │   │   └── Controls.tsx
│   │   ├── hooks/
│   │   │   ├── useSSE.ts
│   │   │   └── useTrades.ts
│   │   └── pages/
│   │       ├── Dashboard.tsx
│   │       └── Analytics.tsx
│   └── vite.config.ts
│
├── mt5-bot/              # reference only, do not modify
└── claude-code-ref/      # reference only, do not modify
```

---

## 11. Key Design Decisions

1. Prompt caching on PLAYBOOK.md reduces Claude cost ~90%
2. Perplexity cached 15min, called only on ATR anomaly
3. MT5 calendar handles 95% of news filtering for free
4. prefilter.py runs free before any paid API call
5. GPT-4o called only on A+ setups (1-2x per day maximum)
6. GPT receives context independently before seeing
   Claude reasoning (genuine unbiased second opinion)
7. Agent and API share SQLite directly (zero-latency sync)
8. SSE chosen over WebSocket (one-way data flow only)
9. Demo/Live switch is config-level only, never simultaneous
10. AI stack is account-blind (equal seriousness always)
11. Magic number 234001 distinguishes agent from mt5-bot
12. All Claude responses parsed as strict JSON always
13. Every decision logged regardless of outcome
14. Cooling period enforced: 20min normal, 30min after loss
15. TP1 hit triggers partial close + SL to breakeven
16. Outside trading windows: zero external API calls
17. mt5-bot and claude-code-ref are reference only,
    never modified

## 12. XAUUSD Points Definition

For all SL, TP, and distance calculations in this system:

- 1 point = $0.01 price movement on XAUUSD
- 10 points = $0.10 price movement
- 100 points = $1.00 price movement

Examples:

- Entry: 4693.50, SL: 4678.00 = 150 points distance
- SL minimum: 8 points = $0.08 price distance
- SL maximum: 50 points = $0.50 price distance

In code always calculate as:
sl_points = abs(entry_price - sl_level) \* 100

Lot size calculation:
risk_usd = account_balance _ max_risk_pct
sl_value_per_lot = sl_points _ 1.0
lot_size = risk_usd / sl_value_per_lot
lot_size = round(lot_size, 2)
lot_size = max(0.01, lot_size)

Never use "pips" terminology in this codebase.
Always use "points" as defined above.

---

## 13. Concurrency Model

The agent uses a single-threaded synchronous model
with one exception: TP1 monitoring.

### Main Loop (synchronous)

- Runs in main thread
- Blocks on wait_for_next_m15()
- Executes full pipeline sequentially
- No asyncio in main loop

### TP1 Monitoring (background thread)

- Runs in a separate daemon thread
- Started by executor.py after trade placement
- Checks open position every 30 seconds
- When TP1 hit:
  - Closes 50% of position
  - Modifies SL to breakeven
  - Sends Telegram tp1_hit notification
  - Logs update to agent_trades
  - Thread exits
- One monitor thread per open position maximum
- Thread is daemon=True so it dies with main process

### Database Concurrency

- SQLite handles concurrent reads safely
- All writes use check_same_thread=False
- All write operations wrapped in try/except
- No connection pooling needed (single writer)
- Use WAL mode for better concurrent access:
  PRAGMA journal_mode=WAL

### Threading Rules

- Main loop never waits on monitor thread
- Monitor thread never calls main loop functions
- Both share database via separate connections
- Both share notifier via thread-safe queue

---

## 14. Circuit Breaker Policy

Defines what happens when external APIs fail repeatedly.

### Claude API Circuit Breaker

- Retry: up to 3 attempts with exponential backoff
  (2s, 4s, 8s between retries)
- After 3 failures: return SKIP with reason
  "Claude API unavailable"
- Log full error each attempt
- Send Telegram alert after first failure
- Do NOT crash main loop
- Reset: next M15 cycle starts fresh

### GPT API Circuit Breaker

- Retry: up to 2 attempts with exponential backoff
  (2s, 4s between retries)
- After 2 failures: default to CONFIRM
  (do not block A+ execution on GPT failure)
- Log full error each attempt
- Send Telegram alert after failure
- Note in decision record: gpt_verdict = "API_FAILED"

### Perplexity Circuit Breaker

- Retry: 1 attempt only
- On failure: default to LOW risk, continue
- Log error silently
- Do not send Telegram (non-critical path)

### MT5 Connection Circuit Breaker

- On disconnect: attempt reconnect every 60 seconds
- After 5 failed reconnects: send Telegram critical alert
- Keep retrying every 5 minutes indefinitely
- Do not attempt any trades while disconnected
- Log every reconnect attempt

### General Policy

- External API failures never crash the main loop
- Every failure is logged with full error detail
- Telegram alerts for critical path failures only
  (Claude, MT5 — not GPT or Perplexity)
- State machine: if agent cannot function, it sleeps
  and retries rather than erroring out

---

## 15. Logging Specification

### Log Levels

- DEBUG: detailed step-by-step (--debug flag only)
- INFO: normal operations, decisions, trades
- WARNING: API failures, retries, unusual conditions
- ERROR: critical failures requiring attention
- CRITICAL: MT5 disconnect, daily limit hit

### Log Format

All logs use structured format:

```
{timestamp} | {level} | {module} | {message} | {data}
```

Example:

```
2026-01-20 12:34:56 | INFO | prefilter | FAIL |
  {"reason": "mid_range", "position_pct": 52.3}

2026-01-20 12:35:15 | INFO | claude_agent | A+ |
  {"direction": "BUY", "confidence": 82,
   "entry": 4693.50}

2026-01-20 12:35:16 | INFO | executor | PLACED |
  {"ticket": 234001, "lots": 0.02, "sl": 4678.00}
```

### Log Files

- Location: agent/logs/
- Filename: agent_YYYY-MM-DD.log
- Rotation: new file each day
- Retention: keep last 30 days
- Max size per file: 50MB

### Log Rules

- Never log API keys or credentials
- Never log full MT5 passwords
- Log account balance as number only
- Log all Claude responses in DEBUG only
  (can contain sensitive reasoning)
- Log all GPT responses in DEBUG only
- Always log skip reasons with specific values
- Always log trade placements with full parameters

### Implementation

Use Python logging module with RotatingFileHandler:

- logging.handlers.TimedRotatingFileHandler
- when='midnight', backupCount=30
- encoding='utf-8'

---

## 16. Claude Response JSON Contract

This is the strict contract between claude_agent.py
and all downstream modules. Claude must always return
this exact structure. claude_agent.py must validate
every field before passing downstream.

```python
{
    # Required fields — always present
    "grade": str,          # "A+" | "B" | "SKIP"
    "direction": str,      # "BUY" | "SELL" | "WAIT"
    "confidence": int,     # 0-100
    "window": str,         # "WINDOW_1"|"WINDOW_2"|"OUTSIDE"
    "pillar_trend": str,   # "PASS" | "WARN" | "FAIL"
    "pillar_momentum": str,# "PASS" | "WARN" | "FAIL"
    "pillar_location": str,# "PASS" | "WARN" | "FAIL"
    "reasoning": str,      # max 3 sentences
    "session_context": str,# one sentence

    # Conditional fields — required if grade is A+ or B
    "entry_price": float,  # exact entry e.g. 4693.50
    "entry_zone": str,     # range e.g. "4691.00-4695.00"
    "sl": float,           # stop loss e.g. 4678.00
    "tp1": float,          # first target e.g. 4715.00
    "tp2": float,          # second target e.g. 4740.00
    "invalidation": str,   # e.g. "M15 close below 4678"
    "base_zone": str,      # e.g. "4688.00-4692.00"
    "setup_type": str,     # one of:
                           # "base_retest"
                           # "session_extreme"
                           # "breakout_retest"
                           # "stop_hunt_reversal"
                           # "absorption_expansion"

    # Conditional fields — required if grade is SKIP
    "skip_reason": str,    # specific reason for skip
}
```

### Validation Rules in claude_agent.py

```python
REQUIRED_ALWAYS = [
    "grade", "direction", "confidence",
    "window", "pillar_trend", "pillar_momentum",
    "pillar_location", "reasoning", "session_context"
]

REQUIRED_IF_TRADEABLE = [
    "entry_price", "entry_zone", "sl",
    "tp1", "tp2", "invalidation",
    "base_zone", "setup_type"
]

REQUIRED_IF_SKIP = ["skip_reason"]

VALID_GRADES = ["A+", "B", "SKIP"]
VALID_DIRECTIONS = ["BUY", "SELL", "WAIT"]
VALID_PILLARS = ["PASS", "WARN", "FAIL"]
VALID_WINDOWS = ["WINDOW_1", "WINDOW_2", "OUTSIDE"]
VALID_SETUP_TYPES = [
    "base_retest", "session_extreme",
    "breakout_retest", "stop_hunt_reversal",
    "absorption_expansion"
]

def validate_response(parsed: dict) -> tuple(bool, str):
    # Check required always fields present
    # Check grade is valid
    # Check direction is valid
    # Check pillar values are valid
    # Check confidence is 0-100 integer
    # If grade A+ or B: check tradeable fields present
    # If grade A+ or B: validate price logic
    #   (sl < entry for BUY, sl > entry for SELL)
    #   (tp1 > entry for BUY, tp1 < entry for SELL)
    #   (tp2 > tp1 for BUY, tp2 < tp1 for SELL)
    #   (sl_points between 8 and 50)
    # If grade SKIP: check skip_reason present
    # Returns (True, "") or (False, "reason")
```

### On Validation Failure

- Log full raw Claude response at ERROR level
- Return SKIP with reason "Invalid Claude response"
- Do not crash
- Do not retry (malformed response unlikely to improve)
- Send Telegram warning if happens 3+ times in one day
