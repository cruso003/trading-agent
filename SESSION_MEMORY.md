# Session Memory & Pattern Recognition — Build Plan

**Created:** 2026-04-10
**Status:** Phase 1 complete. Phase 2 scheduled: 2026-07-01 (minimum 3 months live data required).

---

## What Has Been Built (Phase 1 — April 2026)

### Session Summary Storage
Every time a trading window closes, the system automatically writes a structured
summary to the `session_summaries` table in SQLite:

- Date, window name, session label
- Session high, low, range in points
- Market character: TRENDING / RANGING / COMPRESSING / VOLATILE
- Cycle counts: total, prefilter passes, Claude calls, trades taken
- Session P&L
- H4 direction at close
- Top 3 prefilter/skip reason categories

### Claude Context (Last 3 Sessions)
Every Claude analysis now receives the last 3 completed session summaries.
Claude uses these to understand recent market character, prior session
highs/lows as structural levels, and whether energy is building or releasing.

### Telegram Notifications
Three new notification types:
1. **Window open ping** — fires once when each window begins
2. **Claude SKIP** — fires every time Claude analyses and passes on a setup
3. **Session digest** — fires at window close with full summary

---

## Phase 2 — Pattern Recognition Engine

**Start date: 2026-07-01 (earliest)**

**Why not before:**
Pattern recognition requires a minimum dataset to be meaningful.
With 2 windows per day, 5 trading days per week, 3 months = ~130 sessions.
Below ~80 sessions, any "pattern" is statistical noise.
Do not start Phase 2 before 80 sessions are logged.

Check the session count before starting:
```sql
SELECT COUNT(*) FROM session_summaries;
```

---

## Phase 2 Prerequisites

### Data requirements
- Minimum 80 completed session summaries in the database
- At least 30 TRENDING sessions and 30 RANGING sessions for meaningful comparison
- At least 10 executed trades with outcomes logged (profit/loss, exit reason)
- No major schema changes to `session_summaries` or `agent_decisions` tables

### Infrastructure requirements
- Python `numpy` and `scikit-learn` installed in venv (for similarity scoring)
  OR a simpler rule-based approach (see Approach B below)
- The agent must have been running in live/demo mode continuously —
  forward-fill gaps in session history are not valid training data

### Knowledge requirements
- Review 3 months of session logs before building
- Identify manually which session patterns preceded the best setups
- That manual review informs what the pattern matcher should look for

---

## Phase 2 — What to Build

### Approach A: Embedding-based similarity (advanced)
Match current session conditions against historical sessions using
vector similarity. Requires:
- `sentence-transformers` or a lightweight embedding model
- Session summaries converted to text descriptions
- Cosine similarity search over last 6 months of sessions

**When to use:** If the manual review (above) reveals non-obvious patterns
that rules cannot capture. High complexity, high potential.

### Approach B: Rule-based pattern detection (recommended first)
Define named patterns based on what manual review reveals. Examples:

**Compression breakout:**
- Last 2 sessions: character = COMPRESSING
- Current session: H4 direction unchanged, ATR expanding
- Outcome: high probability of TRENDING session
- Action: Claude weighting note added to context

**Consecutive ranging fade:**
- Last 3 sessions: all RANGING, same H4 direction
- Session highs declining (or lows rising)
- Outcome: potential H4 direction change incoming
- Action: Claude warned to weight trend pillar less

**Session trap setup:**
- Prior Asia: TRENDING (large range)
- Prior London: reversed Asia direction
- Current: H4 still in Asia direction
- Outcome: watch for London trap reversal
- Action: Claude context note on trap probability

**Why Approach B first:** It's auditable, explainable, and can be validated
against actual session outcomes in the database. If a pattern says
"compression breakout likely" and it keeps failing, you remove it.
With embedding similarity you cannot do that inspection easily.

---

## Phase 2 — Implementation Steps

1. **Manual review** (before writing any code)
   - Export 3 months of session summaries to CSV
   - Review alongside actual price charts for each session
   - Write down 3-5 patterns you observe with specific conditions
   - Validate each pattern against at least 10 historical examples

2. **Pattern definition file** (`agent/patterns.py`)
   - Each pattern is a named function that takes recent session summaries
   - Returns: `{matched: bool, pattern_name: str, context_note: str}`
   - No ML, just conditional logic from manual review

3. **Integration into context builder** (`agent/context.py`)
   - Call `detect_patterns(recent_sessions)` after session summaries fetched
   - Add `detected_patterns` list to Claude's context package

4. **PLAYBOOK.md update**
   - Document each named pattern and what it means for analysis
   - Claude uses pattern names to adjust confidence weighting

5. **Validation loop** (ongoing)
   - After 30 more sessions with pattern detection active
   - Check: did detected patterns precede better/worse setups?
   - Adjust or remove patterns that don't improve outcomes

---

## Phase 2 — What NOT to Build

- Do not build a system that auto-adjusts Claude's thresholds based on patterns
  (e.g. "compression detected, lower confidence requirement to 60")
  Claude must still apply the full playbook. Patterns are context, not overrides.

- Do not try to predict specific price levels from historical sessions.
  Prior session high/low is already in context. That's enough.

- Do not use more than the last 10 sessions for pattern detection.
  Gold market structure shifts. A 6-month-old pattern from a different
  macro regime is noise, not signal.

- Do not build this before the data exists. A pattern engine with 40 sessions
  of data will hallucinate patterns and degrade Claude's decision quality.

---

## Files Involved

| File | Phase 1 | Phase 2 |
|---|---|---|
| `agent/database.py` | `session_summaries` table + methods | Read patterns from history |
| `agent/notifier.py` | window open, claude skip, digest | Pattern alert (optional) |
| `agent/context.py` | recent_sessions in Claude context | detected_patterns in context |
| `agent/main.py` | session tracker, flush on close | No change |
| `agent/patterns.py` | Not yet created | Pattern detection logic |
| `PLAYBOOK.md` | Recent session context section | Named pattern definitions |

---

## Milestone Checklist

- [x] Session summaries written to DB at window close
- [x] Last 3 sessions passed to Claude in context
- [x] Telegram: window open, Claude skip, session digest
- [ ] 80 session summaries in database (check: `SELECT COUNT(*) FROM session_summaries`)
- [ ] Manual review of 3 months of session data
- [ ] Identify 3-5 reproducible patterns with historical examples
- [ ] Build `agent/patterns.py` with rule-based detection
- [ ] Add `detected_patterns` to Claude context
- [ ] Update PLAYBOOK.md with pattern definitions
- [ ] Run 30 sessions with pattern detection active
- [ ] Validate pattern accuracy vs outcomes

---

*Review this document before starting Phase 2.
The start date is a minimum, not a target — only begin when the data and
manual review are both complete.*
