"""
GoldTrader AI Agent — Analytics Routes
Reference: ARCHITECTURE.md Section 6
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/analytics/summary")
async def get_summary(request: Request):
    """
    GET /api/analytics/summary — overall performance metrics
    Returns: total trades, win rate, P&L, A+/B/SKIP counts, GPT challenges
    """
    state = request.app.state.agent_state
    return state.get_analytics_summary()


@router.get("/analytics/windows")
async def get_windows(request: Request):
    """
    GET /api/analytics/windows — performance by trading window
    Returns: window_performance table data
    """
    state = request.app.state.agent_state
    return state.get_analytics_windows()


@router.get("/analytics/daily")
async def get_daily(request: Request, days: int = 30):
    """
    GET /api/analytics/daily — daily P&L history
    Query params: days (default 30)
    """
    state = request.app.state.agent_state
    return state.get_analytics_daily(days=days)


@router.get("/analytics/grades")
async def get_grades(request: Request):
    """
    GET /api/analytics/grades — A+/B/SKIP breakdown with execution rates
    """
    state = request.app.state.agent_state
    return state.get_analytics_grades()
