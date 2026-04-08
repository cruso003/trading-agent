"""
ApexGold Platform — Broadcast Routes
Owner creates broadcasts; mentees read them.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from api.auth import get_current_user, require_owner
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])

# Re-use the same scheme token URL as auth.py
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------


class BroadcastCreate(BaseModel):
    title: str
    message: str
    owner_note: Optional[str] = None
    trade_context: Optional[str] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post("")
async def create_broadcast(
    body: BroadcastCreate,
    request: Request,
    _owner: dict = Depends(require_owner),
):
    """Create a new broadcast (owner only)."""
    platform_db = request.app.state.platform_db

    broadcast_id = platform_db.create_broadcast(
        title=body.title,
        message=body.message,
        owner_note=body.owner_note,
        trade_context=body.trade_context,
    )
    if broadcast_id == -1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create broadcast",
        )

    return {"status": "created", "broadcast_id": broadcast_id}


@router.get("")
async def list_broadcasts(
    request: Request,
    token: str = Depends(_oauth2_scheme),
):
    """Get the last 20 broadcasts (authenticated users)."""
    # Validate authentication
    await get_current_user(request, token)

    platform_db = request.app.state.platform_db
    broadcasts = platform_db.get_broadcasts(limit=20)
    return {"broadcasts": broadcasts, "count": len(broadcasts)}
