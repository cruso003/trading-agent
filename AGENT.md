# GoldTrader AI Agent — Master System Document

## What This Is

An AI-powered trading agent for XAUUSD (Gold) on Exness via MT5.
The agent watches the market 24/7, analyses setups using a proven
trading playbook, and executes trades autonomously in the correct
market windows. A web dashboard provides full visibility and control.

## The Problem It Solves

A manual trading bot (mt5-bot) already exists but lacks:

- Contextual memory of recent setups and outcomes
- Understanding of institutional behavior vs indicator signals
- Ability to re-evaluate before new entries after recent trades
- Knowledge of specific high-value trading windows
- Real-time news/macro context

The trader was bridging this gap manually using GPT analysis.
This agent automates that bridge.

## Environment

- OS: Windows (EliteBook 840 G8)
- Broker: Exness
- Asset: XAUUSD only
- MT5: Demo account + Live account
- Timezone: GMT+0 (Liberia)
- Runtime: Runs continuously on Windows

## Two Trading Windows (GMT+0)

- Window 1 (Asia Open): 23:00 – 01:00
- Window 2 (London-NY Overlap): 12:00 – 14:00
- Outside these windows: agent sleeps, zero API calls

## Agent Behavior

- Monitors every M15 candle close
- Pre-filters using local logic (no API cost)
- Only calls Claude when a potential setup exists
- Only calls Perplexity when Claude analysis is needed
- Auto-executes A+ grade setups only
- Alerts B grade setups via Telegram (manual execution)
- Logs every decision with full reasoning
- Operates on Demo by default, Live requires explicit config

## Three Layers

1. Agent Core (Python) — brain, MT5, execution, Telegram
2. API Layer (FastAPI) — exposes agent state via REST + SSE
3. Dashboard (Vite + React) — visibility and control

## Real-Time Communication

- SSE (Server-Sent Events) for server → dashboard streaming
- REST endpoints for dashboard → server controls
- Rationale: data flows one direction only (agent → dashboard)
  Controls (demo/live toggle, enable/disable) are REST calls
  SSE is simpler, native to browsers, auto-reconnects,
  FastAPI supports natively via EventSourceResponse

## Reference Repositories

- mt5-bot/ — MT5 infrastructure patterns, risk management,
  database schema, Telegram integration
- claude-code-ref/ — Claude API patterns, prompt caching,
  context compaction, retry logic, tool use

## Key Constraints

- Never modify mt5-bot/ or claude-code-ref/
- Magic number for agent trades: 234001
  (mt5-bot uses 234000, must be distinguishable)
- Maximum 2% account balance risk per trade
- Maximum 2 open positions simultaneously
- Daily loss limit enforced before any execution
- Demo and Live never run simultaneously
- Claude API called maximum 2-5 times per session window
- Perplexity called only when Claude analysis is triggered
- Outside trading windows: zero external API calls

## Tech Stack

- Agent Core: Python 3.11+
- MT5: MetaTrader5 Python library
- Claude: Anthropic Python SDK (claude-sonnet-4-6)
- News: Perplexity API
- Notifications: Telegram Bot API
- Database: SQLite
- Backend: FastAPI + SSE (EventSourceResponse)
- Frontend: Vite + React + TypeScript + Tailwind
- Charts: TradingView Lightweight Charts + Recharts

## Build Phases

- Phase 1: Agent core (headless, proven in demo)
- Phase 2: FastAPI + SSE layer
- Phase 3: Vite dashboard

## Current Status

Phase 1 — In progress
See TASKS.md for detailed status
