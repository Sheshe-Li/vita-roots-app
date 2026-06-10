"""
Shared FastAPI dependencies.
"""
from __future__ import annotations

import logging
import os

from fastapi import Header, HTTPException
from supabase import create_client

logger = logging.getLogger(__name__)


def _admin_client():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    return create_client(url, key)


async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Validates a Supabase Bearer token and returns the raw auth user object.
    Use this on routes where the family may not exist yet (e.g. create family).
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        admin = _admin_client()
        resp = admin.auth.get_user(token)
        user = resp.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": str(user.id), "email": user.email}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Token validation error: {exc}")
        raise HTTPException(status_code=401, detail="Token validation failed")


async def get_current_family(authorization: str = Header(...)) -> dict:
    """
    Validates a Supabase Bearer token and returns the authenticated family record.
    Raises 401 if the token is missing or invalid.
    Raises 404 if no family is linked to the auth user.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        admin = _admin_client()
        resp = admin.auth.get_user(token)
        user = resp.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Token validation error: {exc}")
        raise HTTPException(status_code=401, detail="Token validation failed")

    try:
        result = (
            admin.table("families")
            .select("*, family_members(*)")
            .eq("auth_user_id", str(user.id))
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="No family linked to this account")
        family = result.data
        family["members"] = family.pop("family_members", [])
        return family
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Family lookup error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch family")
