"""
GoldTrader AI Agent — Agent Status & Control Routes
Reference: ARCHITECTURE.md Section 6
"""

from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.get("/status")
async def get_status(request: Request):
    """
    GET /api/status — agent current state
    Returns: status, current_window, last_analysis_time, daily_pnl, etc.
    """
    state = request.app.state.agent_state
    return state.get_status()


@router.get("/decisions")
async def get_decisions(request: Request, limit: int = 50, grade: str = None):
    """
    GET /api/decisions — full decision log
    Query params: limit (default 50), grade (A+, B, SKIP)
    """
    state = request.app.state.agent_state
    return state.get_decisions(limit=limit, grade=grade)


@router.post("/control/pause")
async def pause_agent(request: Request):
    """POST /api/control/pause — pause agent."""
    state = request.app.state.agent_state
    state.db.update_agent_state({"status": "paused"})
    state.push_event("agent_status", {"status": "paused"})
    return {"status": "paused"}


@router.post("/control/resume")
async def resume_agent(request: Request):
    """POST /api/control/resume — resume agent."""
    state = request.app.state.agent_state
    state.db.update_agent_state({"status": "watching"})
    state.push_event("agent_status", {"status": "watching"})
    return {"status": "watching"}
