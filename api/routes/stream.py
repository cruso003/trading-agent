"""
GoldTrader AI Agent — SSE Stream Route
Server-Sent Events for real-time dashboard updates.
Reference: ARCHITECTURE.md Section 5
"""

import asyncio
import json
import time
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter()


async def _event_generator(request: Request, queue: list, state):
    """
    Async generator that yields SSE events from the queue.
    Sends heartbeat every 15s to keep connection alive.
    """
    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Drain events from queue
            while queue:
                event = queue.pop(0)
                yield {
                    "event": event["type"],
                    "data": json.dumps(event["data"], default=str),
                }

            # Heartbeat every 15s
            yield {
                "event": "heartbeat",
                "data": json.dumps({"time": time.time()}),
            }

            await asyncio.sleep(1)

    finally:
        state.unsubscribe(queue)


@router.get("/stream")
async def sse_stream(request: Request):
    """
    SSE endpoint for real-time agent state streaming.
    Reference: ARCHITECTURE.md Section 5

    Event types:
      agent_status, window_open, window_closed, prefilter_pass,
      prefilter_fail, news_alert, analysis_done, gpt_confirm,
      gpt_challenge, trade_placed, trade_closed, tp1_hit,
      risk_blocked, b_alert, skip_logged
    """
    state = request.app.state.agent_state
    queue = state.subscribe()

    # Send initial state on connect
    initial_status = state.get_status()
    queue.append({
        "type": "agent_status",
        "data": initial_status,
        "timestamp": time.time(),
    })

    return EventSourceResponse(
        _event_generator(request, queue, state),
        media_type="text/event-stream",
    )
