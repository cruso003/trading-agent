"""
GoldTrader AI Agent — News & Macro Risk
MT5 Economic Calendar (primary, free) + Perplexity API (fallback on ATR anomaly).
Reference: ARCHITECTURE.md Section 3 (news pipeline), Section 14 (circuit breaker)
"""

import json
import logging
import time
import requests
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("news")

# Cache for Perplexity results (avoid redundant calls within 15 min)
_perplexity_cache = {
    "result": None,
    "expires_at": 0,
}


def check_economic_calendar(calendar_events: list) -> dict:
    """
    Evaluate MT5 economic calendar events.
    Input: list from market.get_economic_calendar()
    Returns: {has_high_impact: bool, events: list, next_event_minutes: int|None}
    """
    high_impact = [e for e in calendar_events if e.get("impact") == "HIGH"]

    next_minutes = None
    if high_impact:
        # Find soonest event
        now = datetime.now(timezone.utc)
        for evt in high_impact:
            try:
                if isinstance(evt.get("time"), str):
                    evt_time = datetime.fromisoformat(evt["time"].replace("Z", "+00:00"))
                    diff = (evt_time - now).total_seconds() / 60
                    if next_minutes is None or diff < next_minutes:
                        next_minutes = int(diff)
            except Exception:
                continue

    return {
        "has_high_impact": len(high_impact) > 0,
        "events": high_impact,
        "next_event_minutes": next_minutes,
    }


def check_atr_anomaly(current_atr: float, avg_atr: float) -> bool:
    """
    Check if current ATR is anomalously high (> 2x average).
    This triggers Perplexity lookup for unscheduled events.
    """
    if avg_atr <= 0:
        return False
    return current_atr > (avg_atr * 2.0)


def call_perplexity(api_key: str, context: str = "") -> dict:
    """
    Call Perplexity API for current Gold market news.
    Returns: {risk_level: str, summary: str, should_skip: bool}

    Circuit breaker: 1 attempt only. On failure: LOW risk default.
    Reference: ARCHITECTURE.md Section 14
    """
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a financial news analyst. Respond with JSON only. "
                            "Assess current Gold (XAUUSD) market conditions and news."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"What are the current Gold market news and events affecting XAUUSD right now? "
                            f"Are there any Fed/CPI/NFP/geopolitical events that could cause sharp moves? "
                            f"Context: {context}\n\n"
                            f"Respond in this exact JSON format:\n"
                            f'{{"risk_level": "HIGH" or "MEDIUM" or "LOW", '
                            f'"summary": "one sentence summary", '
                            f'"should_skip": true or false}}'
                        ),
                    },
                ],
                "max_tokens": 200,
            },
            timeout=15,
        )

        if response.status_code != 200:
            logger.warning(f"Perplexity HTTP {response.status_code}")
            return {"risk_level": "LOW", "summary": "Perplexity unavailable", "should_skip": False}

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parse JSON from response
        try:
            # Try direct parse first
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
            else:
                logger.warning("Perplexity response not parseable as JSON")
                return {"risk_level": "LOW", "summary": content[:100], "should_skip": False}

        # Validate required fields
        risk = result.get("risk_level", "LOW").upper()
        if risk not in ("HIGH", "MEDIUM", "LOW"):
            risk = "LOW"

        return {
            "risk_level": risk,
            "summary": result.get("summary", "No summary available"),
            "should_skip": result.get("should_skip", False),
        }

    except Exception as e:
        logger.warning(f"Perplexity call failed: {e}")
        return {"risk_level": "LOW", "summary": f"Perplexity error: {str(e)[:50]}", "should_skip": False}


def get_news_context(
    calendar_events: list,
    current_atr: float,
    avg_atr: float,
    perplexity_api_key: str,
    cache_minutes: int = 15,
) -> dict:
    """
    Orchestrate the full news check pipeline.
    Reference: ARCHITECTURE.md Section 3 (News Check Flow)

    Step 1: Check MT5 Economic Calendar (free)
    Step 2: If no high impact events, check ATR anomaly
    Step 3: If ATR anomalous, call Perplexity (cached)

    Returns: {
        risk_level: str,
        summary: str,
        should_skip: bool,
        calendar_events: list,
        source: str,
    }
    """
    global _perplexity_cache

    # Step 1: MT5 Economic Calendar
    cal_result = check_economic_calendar(calendar_events)

    if cal_result["has_high_impact"]:
        event_names = ", ".join([e.get("name", "?") for e in cal_result["events"][:3]])
        return {
            "risk_level": "HIGH",
            "summary": f"HIGH impact events: {event_names}",
            "should_skip": True,
            "calendar_events": cal_result["events"],
            "source": "mt5_calendar",
        }

    # Step 2: Check ATR anomaly
    is_anomalous = check_atr_anomaly(current_atr, avg_atr)

    if not is_anomalous:
        # Normal conditions: no news risk
        return {
            "risk_level": "LOW",
            "summary": "No high-impact events, normal volatility",
            "should_skip": False,
            "calendar_events": cal_result["events"],
            "source": "mt5_calendar",
        }

    # Step 3: ATR anomaly detected — call Perplexity (with cache)
    now = time.time()
    if _perplexity_cache["result"] and now < _perplexity_cache["expires_at"]:
        logger.debug("Using cached Perplexity result")
        cached = _perplexity_cache["result"]
        cached["source"] = "perplexity_cached"
        cached["calendar_events"] = cal_result["events"]
        return cached

    # Fresh Perplexity call
    context = f"ATR is {current_atr:.2f} vs average {avg_atr:.2f} (anomalous spike)"
    pplx_result = call_perplexity(perplexity_api_key, context)

    # Cache the result
    _perplexity_cache["result"] = pplx_result
    _perplexity_cache["expires_at"] = now + (cache_minutes * 60)

    return {
        "risk_level": pplx_result["risk_level"],
        "summary": pplx_result["summary"],
        "should_skip": pplx_result["should_skip"],
        "calendar_events": cal_result["events"],
        "source": "perplexity",
    }
