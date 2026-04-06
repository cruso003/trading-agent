"""
GoldTrader AI Agent — Trade History Routes
Reference: ARCHITECTURE.md Section 6
"""

from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.get("/trades")
async def get_trades(request: Request, limit: int = 50):
    """
    GET /api/trades — trade history with limit
    Returns list of trades, newest first.
    """
    state = request.app.state.agent_state
    return state.get_trades(limit=limit)


@router.get("/trades/{trade_id}")
async def get_trade(request: Request, trade_id: int):
    """
    GET /api/trades/:id — single trade detail
    """
    state = request.app.state.agent_state
    trade = state.get_trade(trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade
