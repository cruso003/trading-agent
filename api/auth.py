"""
ApexGold Platform — Authentication Routes
JWT-based auth with role support.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# ------------------------------------------------------------------
# JWT configuration
# ------------------------------------------------------------------

JWT_SECRET: str = os.getenv("JWT_SECRET", "apexgold-dev-secret-change-in-production")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS: int = 24

# ------------------------------------------------------------------
# Password hashing
# ------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ------------------------------------------------------------------
# OAuth2 scheme
# ------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    invite_code: str


class ApplicationRequest(BaseModel):
    name: str
    email: str
    country: str
    experience: str  # 'none' | 'beginner' | 'intermediate'
    reason: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str


class SetupOwnerRequest(BaseModel):
    name: str
    email: str
    password: str
    setup_key: str


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload["exp"] = expire
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    platform_db = request.app.state.platform_db
    user = platform_db.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    if user.get("status") == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    return user


async def require_owner(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> dict:
    user = await get_current_user(request, token)
    if user["role"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )
    return user


# ------------------------------------------------------------------
# Router
# ------------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest):
    """Authenticate with email and password, return JWT."""
    platform_db = request.app.state.platform_db
    user = platform_db.get_user_by_email(body.email)

    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.get("status") == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    platform_db.update_user_last_login(user["id"])

    token = create_token({"user_id": user["id"], "role": user["role"]})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        name=user["name"],
    )


@router.post("/register", response_model=TokenResponse)
async def register(request: Request, body: RegisterRequest):
    """Register a new user with a valid invite code."""
    platform_db = request.app.state.platform_db

    invite = platform_db.get_invite(body.invite_code)
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite code",
        )
    if invite["used"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite code has already been used",
        )

    # If the invite is tied to a specific email, enforce it
    if invite["email"] and invite["email"].lower() != body.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invite code is not valid for your email address",
        )

    existing = platform_db.get_user_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    password_hash = hash_password(body.password)
    role = invite.get("role", "mentee")
    user_id = platform_db.create_user(
        name=body.name,
        email=body.email,
        password_hash=password_hash,
        role=role,
        invite_code=body.invite_code,
    )
    if user_id == -1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account",
        )

    platform_db.mark_invite_used(body.invite_code, body.email)

    token = create_token({"user_id": user_id, "role": role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=role,
        name=body.name,
    )


@router.post("/apply")
async def apply(request: Request, body: ApplicationRequest):
    """Submit an application to join the platform."""
    platform_db = request.app.state.platform_db

    existing = platform_db.get_application_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An application for this email address already exists",
        )

    app_id = platform_db.submit_application(
        name=body.name,
        email=body.email,
        country=body.country,
        experience=body.experience,
        reason=body.reason,
    )
    if app_id == -1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit application",
        )

    return {
        "status": "submitted",
        "message": "Application received. You will be contacted when approved.",
    }


@router.get("/me")
async def me(
    request: Request,
    token: str = Depends(oauth2_scheme),
):
    """Return the currently authenticated user (without password hash)."""
    user = await get_current_user(request, token)
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return safe_user


@router.post("/setup-owner", response_model=TokenResponse)
async def setup_owner(request: Request, body: SetupOwnerRequest):
    """
    First-run only: create the owner account.
    Only succeeds when zero users exist in the database.
    """
    expected_setup_key = os.getenv("SETUP_KEY", "apexgold-setup")
    if body.setup_key != expected_setup_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid setup key",
        )

    platform_db = request.app.state.platform_db

    if platform_db.user_count() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner account already exists. Setup endpoint is disabled.",
        )

    password_hash = hash_password(body.password)
    created = platform_db.init_owner(
        name=body.name,
        email=body.email,
        password_hash=password_hash,
    )
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create owner account",
        )

    user = platform_db.get_user_by_email(body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Owner created but could not be retrieved",
        )

    token = create_token({"user_id": user["id"], "role": "owner"})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role="owner",
        name=body.name,
    )
