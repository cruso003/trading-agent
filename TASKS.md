# GoldTrader AI Agent — Build Tasks

# Read AGENT.md and ARCHITECTURE.md before touching any task.

# Update this file as tasks are completed.

# Every Claude Code session starts by reading this file.

---

## Current Phase

PHASE 1 — Agent Core (Headless)

---

## Phase 1: Agent Core

### Status Legend

⬜ Not started
🔄 In progress  
✅ Complete
❌ Blocked (reason below)

---

### Setup & Configuration

✅ TASK-001: Project initialization (2026-04-05)

- Created trading_agent/ directory structure
  exactly as defined in ARCHITECTURE.md
- Created requirements.txt with all dependencies:
  MetaTrader5, anthropic, openai, requests,
  python-dotenv, fastapi, uvicorn, schedule
- Created .env.example with all variables
  (no real values, just keys)
- Created .gitignore (exclude .env, agent/data/,
  **pycache**, \*.pyc)
- Reference: ARCHITECTURE.md Section 10

✅ TASK-002: config.py (2026-04-05)

- Load all .env variables
- Validate all required keys present on startup
- Expose typed settings object to all modules
- Fail loudly if any required key is missing
- Never hardcode any value
- Reference: ARCHITECTURE.md Section 9

---

### Core Infrastructure

✅ TASK-003: database.py (2026-04-05)

- Create SQLite database at DB_PATH from config
- Create all four tables on first run:
  agent_decisions, agent_trades,
  window_performance, agent_state
- Schema exactly as defined in ARCHITECTURE.md
  Section 4
- Functions needed:
  - log_decision(decision_dict) → int (decision_id)
  - log_trade(trade_dict) → int (trade_id)
  - update_trade(ticket_id, update_dict) → bool
  - get_recent_decisions(n=5) → list
  - get_recent_trades(n=3) → list
  - get_daily_pnl() → float
  - get_open_positions_count() → int
  - update_agent_state(state_dict) → bool
  - update_window_performance(date, window, data)
- Reference: ARCHITECTURE.md Section 4

✅ TASK-004: windows.py (2026-04-05)

- Detect current trading window from GMT+0 time
- Window 1: 23:00-01:00 (handles midnight crossover)
- Window 2: 12:00-14:00
- Functions needed:
  - get_current_window() → str or None
  - is_tradeable_time() → bool
  - minutes_into_window() → int
  - time_to_next_window() → dict
  - get_window_name(window_id) → str
- Handle midnight crossover for Window 1 correctly
- No external dependencies
- Reference: ARCHITECTURE.md Section 8

✅ TASK-005: notifier.py (2026-04-05)

- Telegram Bot API integration
- All templates exactly as defined in
  ARCHITECTURE.md Section 7
- Functions needed:
  - send_message(text) → bool
  - send_trade_placed(trade_dict) → bool
  - send_b_alert(analysis_dict) → bool
  - send_gpt_challenge(analysis_dict) → bool
  - send_risk_blocked(reason, decision_id) → bool
  - send_news_alert(news_summary) → bool
  - send_skip(reason) → bool
  - send_tp1_hit(trade_dict) → bool
  - send_agent_status(status) → bool
- Never crash main loop on Telegram failure
- Log all send failures silently
- Reference: ARCHITECTURE.md Section 7

---

### Market Data & Analysis

✅ TASK-006: market.py (2026-04-05)

- MT5 connection and data fetching
- Use MetaTrader5 Python library
- Functions needed:
  - connect() → bool
  - disconnect() → None
  - is_connected() → bool
  - get_candles(symbol, timeframe, count) → list
  - get_current_price(symbol) → dict
  - get_account_info() → dict (balance only, no label)
  - get_open_positions(magic=234001) → list
  - get_economic_calendar(hours_ahead=1) → list
  - wait_for_next_m15() → None (blocks until close)
- Symbol: XAUUSD always
- Magic number: 234001
- Reference: ARCHITECTURE.md Section 3,
  mt5-bot/src for connection patterns

✅ TASK-007: indicators.py (2026-04-05)

- Calculate all technical indicators from raw candles
- Functions needed:
  - calculate_ema(candles, period) → list
  - calculate_rsi(candles, period=14) → float
  - calculate_macd(candles) → dict
  - calculate_atr(candles, period=14) → float
  - calculate_body_ratio(candle) → float
  - calculate_strength(ema_fast, ema_slow) → float
  - get_session_levels(candles_h1) → dict
  - get_price_position(price, high, low) → float
  - get_m30_sequence(candles_m30, count=5) → list
  - analyse_timeframe(candles, tf_name) → dict
- Strength score: 0-10 scale (EMA distance based)
- Body ratio: 0-100% (body vs total range)
- Price position: 0-100% (where in session range)
- Reference: mt5-bot/src/trading_bot for patterns

✅ TASK-008: news.py (2026-04-05)

- MT5 Economic Calendar + Perplexity fallback
- Functions needed:
  - check_economic_calendar() → dict
    Returns: {has_high_impact, events_list,
    next_event_minutes}
  - check_atr_anomaly(current_atr, avg_atr) → bool
  - call_perplexity(context) → dict
    Returns: {risk_level, summary, should_skip}
  - get_news_context(current_atr, avg_atr) → dict
    Orchestrates both checks, returns final risk
- Cache Perplexity result 15 minutes
- If Perplexity fails: return LOW risk, log error
- HIGH impact events: Fed, CPI, NFP, Rate decisions
- Reference: ARCHITECTURE.md Section 2

✅ TASK-009: prefilter.py (2026-04-05)

- Zero API cost local signal gate
- Must run before any paid API call
- Functions needed:
  - run_prefilter(indicators_dict,
    window_status, db) → tuple(bool, str)
    Returns (passed, reason_if_failed)
- Checks in order:
  1. H4 and H1 direction agree
  2. M30 body strength not 40-55% (dead zone)
  3. Not in post-trade cooling period
     (20min normal, 30min after loss)
  4. Price not mid-range (position 35-65%)
  5. No open position in same direction already
- Log every failure with specific reason
- Reference: ARCHITECTURE.md Section 3,
  PLAYBOOK.md Three Pillars

✅ TASK-010: context.py (2026-04-05)

- Build the full context package sent to Claude
- Functions needed:
  - build_context(
    indicators_dict,
    window_status,
    account_info,
    news_context,
    db
    ) → dict
- Context package must include:
  - timestamp, session, window_status,
    minutes_into_window
  - H4, H1, M30, M15 indicator dicts
  - Last 5 M30 candle sequence
  - Session high, low, price_position_pct
  - Asia high, Asia low if available
  - account_balance (number only, no label)
  - daily_pnl, open_positions_count
  - last_5_decisions from database
  - last_3_trades from database
  - news_risk_level, news_summary,
    calendar_events_next_60min
- Reference: PLAYBOOK.md Context Package section

---

### AI Integration

✅ TASK-011: claude_agent.py (2026-04-05)

- Claude API integration with prompt caching
- Load PLAYBOOK.md as system prompt
- Apply cache_control: ephemeral to system prompt
- Functions needed:
  - analyse(context_dict) → dict
    Returns parsed JSON decision
  - \_build_user_message(context_dict) → str
  - \_parse_response(response) → dict
  - \_validate_response(parsed_dict) → bool
- Model: CLAUDE_MODEL from config
- Always parse response as strict JSON
- If JSON parse fails: return SKIP with error reason
- Retry up to 3 times on API failure (use backoff)
- Log full Claude response for debugging
- Reference: claude-code-ref/src/claude.ts
  for API patterns and retry logic
  ARCHITECTURE.md Section 2

✅ TASK-012: gpt_agent.py (2026-04-05)

- GPT-4o second opinion (A+ setups only)
- Functions needed:
  - verify(context_dict, claude_analysis) → dict
    Returns {verdict: CONFIRM|CHALLENGE,
    reasoning: str}
  - \_build_prompt(context_dict,
    claude_analysis) → str
  - \_parse_response(response) → dict
- GPT must NOT see Claude reasoning in prompt
  Send context_dict raw, Claude analysis separate
  as "a previous analysis to verify"
- Model: GPT_MODEL from config
- Retry up to 2 times on API failure
- If GPT fails: default to CONFIRM, log error
  (do not block execution on GPT failure)
- Reference: ARCHITECTURE.md Section 2

---

### Execution & Risk

✅ TASK-013: risk.py (2026-04-05)

- Pre-execution risk validation
- Functions needed:
  - validate(
    direction,
    entry_price,
    sl_level,
    db,
    account_info
    ) → tuple(bool, str)
    Returns (passed, reason_if_failed)
  - calculate_lot_size(
    account_balance,
    sl_points,
    max_risk_pct=0.02
    ) → float
  - get_sl_points(entry_price, sl_level) → float
  - is_daily_limit_reached(db) → bool
  - is_max_positions_reached(market) → bool
- Lot size: round to 0.01 minimum
- SL distance: must be 8-50 points
- Daily limit: sum of today's closed losses
- Reference: ARCHITECTURE.md Section 8

✅ TASK-014: executor.py (2026-04-05)

- MT5 order placement and position management
- Functions needed:
  - place_trade(
    direction,
    lot_size,
    sl,
    tp1,
    tp2,
    comment
    ) → tuple(bool, int, str)
    Returns (success, ticket_id, error_msg)
  - close_trade(ticket_id) → bool
  - modify_sl(ticket_id, new_sl) → bool
  - get_position(ticket_id) → dict or None
  - monitor_tp1(ticket_id, tp1_level) → None
    Runs in background, closes 50% at TP1,
    moves SL to breakeven
  - check_positions() → list
- Magic number: 234001 always
- Verify every order after placement
- Never assume success without verification
- Reference: mt5-bot/src for execution patterns
  ARCHITECTURE.md Section 8

---

### Main Loop

✅ TASK-015: main.py (2026-04-05)

- Entry point and main orchestration loop
- Imports and orchestrates all modules
- Main loop flow exactly as ARCHITECTURE.md
  Section 3 pipeline
- Additional requirements:
  - Graceful shutdown on CTRL+C
  - Reconnect to MT5 if connection drops
  - Log every step with timestamp
  - Update agent_state in database each cycle
  - Send Telegram on startup and shutdown
  - Handle all exceptions without crashing loop
  - --debug flag prints each step verbosely
  - --dry-run flag runs full pipeline but
    skips actual trade execution
- Reference: ARCHITECTURE.md Section 3

---

### Testing

⬜ TASK-016: Integration test

- Run agent in --dry-run mode for full 24 hours
- Verify:
  - Windows detected correctly at right times
  - Prefilter blocking correctly
  - MT5 connection stable
  - Claude receiving correct context
  - GPT receiving correct context
  - Database logging all decisions
  - Telegram sending all notification types
  - No crashes over 24 hours
- Do not proceed to Phase 2 until this passes

---

## Phase 2: API Gateway

✅ TASK-017: FastAPI setup + state.py (2026-04-06)
✅ TASK-018: SSE stream endpoint (2026-04-06)
✅ TASK-019: Agent status + control routes (2026-04-06)
✅ TASK-020: Trade history routes (2026-04-06)
✅ TASK-021: Analytics routes (2026-04-06)
⬜ TASK-022: Integration test (agent + API)

---

## Phase 3: Dashboard

⬜ TASK-023: Vite + React + Tailwind setup
⬜ TASK-024: useSSE hook
⬜ TASK-025: AgentStatus component
⬜ TASK-026: TradeCard component
⬜ TASK-027: PriceChart component
⬜ TASK-028: AnalysisPanel component
⬜ TASK-029: PerformanceCharts component
⬜ TASK-030: Controls component
⬜ TASK-031: Dashboard page assembly
⬜ TASK-032: Analytics page
⬜ TASK-033: Full system integration test

---

## How to Use This File

### Starting a Claude Code session

Paste this at the start of every session:

"Read AGENT.md, ARCHITECTURE.md, PLAYBOOK.md
and TASKS.md. Your task today is [TASK-XXX].
Follow the architecture exactly.
Reference mt5-bot/ and claude-code-ref/ as noted.
Do not modify reference repositories.
Update TASKS.md when the task is complete."

### Completing a task

When a task is done:

- Change ⬜ to ✅
- Add completion date below the task
- Note any deviations from spec
- Note any new dependencies discovered

### Blocking a task

If a task cannot proceed:

- Change ⬜ to ❌
- Add reason below
- Note what needs to resolve first

### Task order

Tasks within Phase 1 should be built in order.
Each task depends on previous tasks.
Do not skip tasks.
Do not build Phase 2 until Phase 1 TASK-016 passes.
Do not build Phase 3 until Phase 2 TASK-022 passes.
