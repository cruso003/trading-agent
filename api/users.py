"""
ApexGold Platform — User Management Routes (Owner only)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from api.auth import require_owner

router = APIRouter(prefix="/users", tags=["users"])


# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------


class CreateInviteRequest(BaseModel):
    email: Optional[str] = None
    role: str = "mentee"


# ------------------------------------------------------------------
# Applications
# ------------------------------------------------------------------


@router.get("/applications")
async def list_applications(
    request: Request,
    status: Optional[str] = None,
    _owner: dict = Depends(require_owner),
):
    """List all applications. Optionally filter by status (pending/approved/rejected)."""
    platform_db = request.app.state.platform_db
    applications = platform_db.get_applications(status=status)
    return {"applications": applications, "count": len(applications)}


@router.post("/applications/{app_id}/approve")
async def approve_application(
    app_id: int,
    request: Request,
    _owner: dict = Depends(require_owner),
):
    """Approve an application and automatically create an invite for that email."""
    platform_db = request.app.state.platform_db

    applications = platform_db.get_applications()
    app = next((a for a in applications if a["id"] == app_id), None)
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if app["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application is already '{app['status']}'",
        )

    updated = platform_db.update_application_status(app_id, "approved")
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application status",
        )

    invite_code = platform_db.create_invite(email=app["email"], role="mentee")
    if not invite_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application approved but invite creation failed",
        )

    return {
        "status": "approved",
        "app_id": app_id,
        "invite_code": invite_code,
        "invite_email": app["email"],
    }


@router.post("/applications/{app_id}/reject")
async def reject_application(
    app_id: int,
    request: Request,
    _owner: dict = Depends(require_owner),
):
    """Reject an application."""
    platform_db = request.app.state.platform_db

    applications = platform_db.get_applications()
    app = next((a for a in applications if a["id"] == app_id), None)
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if app["status"] == "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application is already rejected",
        )

    updated = platform_db.update_application_status(app_id, "rejected")
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject application",
        )

    return {"status": "rejected", "app_id": app_id}


# ------------------------------------------------------------------
# Mentees
# ------------------------------------------------------------------


@router.get("/mentees")
async def list_mentees(
    request: Request,
    _owner: dict = Depends(require_owner),
):
    """List all mentee and trial users."""
    platform_db = request.app.state.platform_db
    mentees = platform_db.get_mentees()
    # Remove password hashes from response
    safe = [{k: v for k, v in m.items() if k != "password_hash"} for m in mentees]
    return {"mentees": safe, "count": len(safe)}


# ------------------------------------------------------------------
# User management
# ------------------------------------------------------------------


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    request: Request,
    _owner: dict = Depends(require_owner),
):
    """Suspend a user account."""
    platform_db = request.app.state.platform_db

    user = platform_db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user["role"] == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend the owner account",
        )

    updated = platform_db.update_user(user_id, {"status": "suspended"})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend user",
        )

    return {"status": "suspended", "user_id": user_id}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    request: Request,
    _owner: dict = Depends(require_owner),
):
    """Re-activate a suspended user account."""
    platform_db = request.app.state.platform_db

    user = platform_db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updated = platform_db.update_user(user_id, {"status": "active"})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user",
        )

    return {"status": "active", "user_id": user_id}


# ------------------------------------------------------------------
# Invites
# ------------------------------------------------------------------


@router.post("/invites")
async def create_invite(
    body: CreateInviteRequest,
    request: Request,
    _owner: dict = Depends(require_owner),
):
    """Create a standalone invite code."""
    platform_db = request.app.state.platform_db

    code = platform_db.create_invite(email=body.email, role=body.role)
    if not code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invite",
        )

    return {"invite_code": code, "email": body.email, "role": body.role}


@router.get("/invites")
async def list_invites(
    request: Request,
    _owner: dict = Depends(require_owner),
):
    """List all invites."""
    platform_db = request.app.state.platform_db
    invites = platform_db.get_all_invites()
    return {"invites": invites, "count": len(invites)}
