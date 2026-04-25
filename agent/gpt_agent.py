"""
GoldTrader AI Agent — GPT Second Opinion
GPT-4o verification for A+ setups only.
GPT forms independent view WITHOUT seeing Claude reasoning first.
Reference: ARCHITECTURE.md Section 2, Section 14
"""

import json
import logging
import time
from typing import Optional

import openai

logger = logging.getLogger("gpt_agent")


class GPTAgent:
    """
    GPT-4o second opinion for A+ setups.
    Called only when Claude returns A+.
    GPT receives raw market context independently.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def verify(self, context: dict, claude_analysis: dict) -> dict:
        """
        Get GPT's independent verification of an A+ setup.
        Retries up to 2 times with exponential backoff (2s, 4s).

        GPT does NOT see Claude's reasoning — only the proposed trade params.
        Reference: ARCHITECTURE.md Section 14 (circuit breaker)

        Returns: {verdict: "CONFIRM"|"CHALLENGE", reasoning: str}
        """
        prompt = self._build_prompt(context, claude_analysis)

        for attempt in range(1, 3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a Gold (XAUUSD) trading analyst providing a second opinion. "
                                "You will receive current market data and a proposed trade setup. "
                                "Evaluate the setup independently. Respond with JSON only.\n\n"
                                "Your response must be:\n"
                                '{"verdict": "CONFIRM" or "CHALLENGE", "reasoning": "one sentence"}'
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,
                    temperature=0.3,
                )

                raw_text = response.choices[0].message.content or ""
                logger.debug(f"GPT raw response: {raw_text[:300]}")

                parsed = self._parse_response(raw_text)
                if parsed:
                    logger.info(f"{parsed['verdict']} | {parsed['reasoning'][:80]}")
                    return parsed

                # Parse failed but API worked — default CONFIRM
                logger.warning("GPT response not parseable, defaulting to CONFIRM")
                return {"verdict": "CONFIRM", "reasoning": "Response unparseable, defaulting"}

            except openai.RateLimitError as e:
                wait = 2 ** attempt
                logger.warning(f"GPT rate limit (attempt {attempt}/2), waiting {wait}s: {e}")
                time.sleep(wait)

            except openai.APIError as e:
                wait = 2 ** attempt
                logger.warning(f"GPT API error (attempt {attempt}/2), waiting {wait}s: {e}")
                time.sleep(wait)

            except Exception as e:
                logger.error(f"GPT unexpected error (attempt {attempt}/2): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)

        # All attempts failed — default to CONFIRM (do not block execution)
        logger.error("GPT API unavailable after 2 attempts, defaulting to CONFIRM")
        return {"verdict": "CONFIRM", "reasoning": "API_FAILED"}

    def _build_prompt(self, context: dict, claude_analysis: dict) -> str:
        """
        Build GPT prompt with market context and proposed trade.
        GPT sees the trade parameters but NOT Claude's reasoning.
        This ensures an unbiased second opinion.
        """
        # Extract trade parameters only (no reasoning)
        proposed_trade = {
            "direction": claude_analysis.get("direction"),
            "entry_price": claude_analysis.get("entry_price"),
            "sl": claude_analysis.get("sl"),
            "tp1": claude_analysis.get("tp1"),
            "tp2": claude_analysis.get("tp2"),
            "invalidation": claude_analysis.get("invalidation"),
            "setup_type": claude_analysis.get("setup_type"),
            "m15_swing_ref": claude_analysis.get("m15_swing_ref"),
        }

        # Simplified market context
        market_summary = {
            "current_price": context.get("current_price"),
            "spread": context.get("spread"),
            "session": context.get("session"),
            "window": context.get("window_status"),
            "h4_direction": context.get("h4", {}).get("direction"),
            "h4_strength": context.get("h4", {}).get("strength"),
            "h1_direction": context.get("h1", {}).get("direction"),
            "h1_strength": context.get("h1", {}).get("strength"),
            "m30_body_strength": context.get("m30", {}).get("body_strength_ratio"),
            "m15_rsi": context.get("m15", {}).get("rsi"),
            "price_position_pct": context.get("price_position_pct"),
            "session_high": context.get("session_high"),
            "session_low": context.get("session_low"),
            "news_risk": context.get("news_risk_level"),
        }

        return (
            "A previous analysis system has proposed this XAUUSD trade.\n"
            "Evaluate it independently based on the current market data.\n\n"
            f"PROPOSED TRADE:\n{json.dumps(proposed_trade, indent=2)}\n\n"
            f"CURRENT MARKET:\n{json.dumps(market_summary, indent=2)}\n\n"
            "Should this trade be executed? "
            "CONFIRM if the setup is sound, CHALLENGE if you see a problem.\n"
            'Respond only with: {"verdict": "CONFIRM" or "CHALLENGE", "reasoning": "one sentence"}'
        )

    def _parse_response(self, raw_text: str) -> Optional[dict]:
        """Parse GPT response into verdict dict."""
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            # Try extracting JSON from text
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    parsed = json.loads(raw_text[start:end])
                except json.JSONDecodeError:
                    return None
            else:
                return None

        verdict = parsed.get("verdict", "").upper()
        if verdict not in ("CONFIRM", "CHALLENGE"):
            return None

        return {
            "verdict": verdict,
            "reasoning": parsed.get("reasoning", "No reasoning provided"),
        }
