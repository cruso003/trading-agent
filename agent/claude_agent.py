"""
GoldTrader AI Agent — Claude Primary Analyst
Claude API integration with prompt caching and strict JSON validation.
Reference: ARCHITECTURE.md Section 2, Section 14, Section 16
           claude-code-ref/src/claude.ts for API patterns
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import anthropic

logger = logging.getLogger("claude_agent")

# ------------------------------------------------------------------
# Validation constants (ARCHITECTURE.md Section 16)
# ------------------------------------------------------------------

REQUIRED_ALWAYS = [
    "grade", "direction", "confidence",
    "window", "pillar_trend", "pillar_momentum",
    "pillar_location", "reasoning", "session_context",
]

REQUIRED_IF_TRADEABLE = [
    "entry_price", "entry_zone", "sl",
    "tp1", "tp2", "invalidation",
    "base_zone", "setup_type",
]

REQUIRED_IF_SKIP = ["skip_reason"]

VALID_GRADES = ["A+", "B", "SKIP"]
VALID_DIRECTIONS = ["BUY", "SELL", "WAIT"]
VALID_PILLARS = ["PASS", "WARN", "FAIL"]
VALID_WINDOWS = ["WINDOW_1", "WINDOW_2", "OUTSIDE"]
VALID_SETUP_TYPES = [
    "base_retest", "session_extreme",
    "breakout_retest", "stop_hunt_reversal",
    "absorption_expansion",
]


class ClaudeAgent:
    """
    Primary analyst using Claude with prompt caching.
    System prompt (PLAYBOOK.md) is cached via cache_control: ephemeral.
    """

    def __init__(self, api_key: str, model: str, playbook_path: Path):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self._playbook_content = self._load_playbook(playbook_path)

    def _load_playbook(self, path: Path) -> str:
        """Load PLAYBOOK.md content for system prompt."""
        try:
            content = path.read_text(encoding="utf-8")
            logger.info(f"Loaded playbook: {len(content)} chars from {path}")
            return content
        except Exception as e:
            logger.error(f"Failed to load playbook: {e}")
            raise

    def analyse(self, context: dict) -> dict:
        """
        Send context to Claude, get structured analysis.
        Retries up to 3 times with exponential backoff (2s, 4s, 8s).
        Reference: ARCHITECTURE.md Section 14 (circuit breaker)

        Returns parsed and validated JSON decision, or SKIP on failure.
        """
        user_message = self._build_user_message(context)

        for attempt in range(1, 4):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=[
                        {
                            "type": "text",
                            "text": self._playbook_content,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=[
                        {"role": "user", "content": user_message},
                    ],
                )

                # Extract text content
                raw_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        raw_text += block.text

                logger.debug(f"Claude raw response: {raw_text[:500]}")

                # Parse JSON
                parsed = self._parse_response(raw_text)
                if parsed is None:
                    return self._skip_response("Invalid JSON from Claude")

                # Validate
                valid, reason = self._validate_response(parsed)
                if not valid:
                    logger.error(f"Claude validation failed: {reason}")
                    logger.error(f"Raw response: {raw_text[:1000]}")
                    return self._skip_response(f"Invalid Claude response: {reason}")

                logger.info(
                    f"{parsed['grade']} | "
                    f"direction={parsed['direction']}, "
                    f"confidence={parsed['confidence']}"
                )
                return parsed

            except anthropic.RateLimitError as e:
                wait = 2 ** attempt
                logger.warning(f"Claude rate limit (attempt {attempt}/3), waiting {wait}s: {e}")
                time.sleep(wait)

            except anthropic.APIError as e:
                wait = 2 ** attempt
                logger.warning(f"Claude API error (attempt {attempt}/3), waiting {wait}s: {e}")
                time.sleep(wait)

            except Exception as e:
                logger.error(f"Claude unexpected error (attempt {attempt}/3): {e}")
                if attempt < 3:
                    time.sleep(2 ** attempt)

        # All 3 attempts failed
        logger.error("Claude API unavailable after 3 attempts")
        return self._skip_response("Claude API unavailable")

    def _build_user_message(self, context: dict) -> str:
        """
        Format context dict as the user message for Claude.
        Serialized as clean JSON that Claude can parse.
        """
        return (
            "Analyse this market context and return your JSON decision.\n\n"
            f"```json\n{json.dumps(context, indent=2, default=str)}\n```"
        )

    def _parse_response(self, raw_text: str) -> Optional[dict]:
        """Extract JSON from Claude's response text."""

        def _try(text: str) -> Optional[dict]:
            try:
                return json.loads(text)
            except (json.JSONDecodeError, ValueError):
                return None

        # 1. Direct parse
        result = _try(raw_text.strip())
        if result is not None:
            return result

        # 2. Strip markdown code fences (handles \r\n via splitlines())
        stripped = raw_text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            # Find closing fence from the end
            close_idx = None
            for i in range(len(lines) - 1, 0, -1):
                if lines[i].strip() == "```":
                    close_idx = i
                    break
            if close_idx is not None and close_idx > 1:
                content = "\n".join(lines[1:close_idx])
            else:
                content = "\n".join(lines[1:])  # at least drop opening fence
            result = _try(content.strip())
            if result is not None:
                return result

        # 3. Brace extraction fallback (first { to last })
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start >= 0 and end > start:
            result = _try(raw_text[start:end])
            if result is not None:
                return result

        logger.error(
            f"Could not parse JSON from Claude response (len={len(raw_text)}): "
            f"{raw_text[:500]}"
        )
        return None

    def _validate_response(self, parsed: dict) -> tuple:
        """
        Validate Claude's response against the JSON contract.
        Reference: ARCHITECTURE.md Section 16
        Returns (True, "") or (False, "reason")
        """
        # Check required always fields
        for field in REQUIRED_ALWAYS:
            if field not in parsed or parsed[field] is None:
                return (False, f"Missing required field: {field}")

        # Validate grade
        grade = parsed.get("grade")
        if grade not in VALID_GRADES:
            return (False, f"Invalid grade: {grade}")

        # Validate direction
        direction = parsed.get("direction")
        if direction not in VALID_DIRECTIONS:
            return (False, f"Invalid direction: {direction}")

        # Validate pillars
        for pillar in ["pillar_trend", "pillar_momentum", "pillar_location"]:
            if parsed.get(pillar) not in VALID_PILLARS:
                return (False, f"Invalid {pillar}: {parsed.get(pillar)}")

        # Validate confidence
        confidence = parsed.get("confidence")
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 100:
            return (False, f"Invalid confidence: {confidence}")

        # Validate window
        if parsed.get("window") not in VALID_WINDOWS:
            return (False, f"Invalid window: {parsed.get('window')}")

        # Conditional: tradeable setup (A+ or B)
        if grade in ("A+", "B"):
            for field in REQUIRED_IF_TRADEABLE:
                if field not in parsed or parsed[field] is None:
                    return (False, f"Grade {grade} missing tradeable field: {field}")

            # Validate setup_type
            if parsed.get("setup_type") not in VALID_SETUP_TYPES:
                return (False, f"Invalid setup_type: {parsed.get('setup_type')}")

            # Validate price logic
            entry = parsed.get("entry_price", 0)
            sl = parsed.get("sl", 0)
            tp1 = parsed.get("tp1", 0)
            tp2 = parsed.get("tp2", 0)

            if direction == "BUY":
                if sl >= entry:
                    return (False, f"BUY: SL ({sl}) must be below entry ({entry})")
                if tp1 <= entry:
                    return (False, f"BUY: TP1 ({tp1}) must be above entry ({entry})")
                if tp2 <= tp1:
                    return (False, f"BUY: TP2 ({tp2}) must be above TP1 ({tp1})")
            elif direction == "SELL":
                if sl <= entry:
                    return (False, f"SELL: SL ({sl}) must be above entry ({entry})")
                if tp1 >= entry:
                    return (False, f"SELL: TP1 ({tp1}) must be below entry ({entry})")
                if tp2 >= tp1:
                    return (False, f"SELL: TP2 ({tp2}) must be below TP1 ({tp1})")

            # Validate SL distance (8-50 points, 1 point = $0.01)
            sl_points = abs(entry - sl) * 100
            if sl_points < 8 or sl_points > 50:
                return (False, f"SL distance {sl_points:.0f} points outside 8-50 range")

        # Conditional: SKIP
        if grade == "SKIP":
            for field in REQUIRED_IF_SKIP:
                if field not in parsed or not parsed[field]:
                    return (False, f"SKIP missing field: {field}")

        return (True, "")

    def _skip_response(self, reason: str) -> dict:
        """Generate a SKIP response for error conditions."""
        return {
            "grade": "SKIP",
            "direction": "WAIT",
            "confidence": 0,
            "window": "OUTSIDE",
            "pillar_trend": "FAIL",
            "pillar_momentum": "FAIL",
            "pillar_location": "FAIL",
            "reasoning": reason,
            "session_context": "Error condition",
            "skip_reason": reason,
            "entry_price": None,
            "entry_zone": None,
            "sl": None,
            "tp1": None,
            "tp2": None,
            "invalidation": None,
            "base_zone": None,
            "setup_type": None,
        }
