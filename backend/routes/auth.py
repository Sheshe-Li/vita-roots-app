"""
Auth route — resolves a Supabase JWT to the caller's family record.
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Header
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter()


def _admin_client():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return create_client(url, key)


@router.get("/families/me")
async def get_my_family(authorization: str = Header(...)):
    """
    Accepts  Authorization: Bearer <supabase_access_token>
    Returns the family record linked to that auth user.
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

    # Look up family by auth_user_id
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
        row = result.data
        row["members"] = row.pop("family_members", [])
        return {"data": row}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Family lookup error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch family")
