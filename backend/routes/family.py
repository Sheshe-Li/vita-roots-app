"""
Family CRUD routes.
POST   /api/families                              — create family
GET    /api/families                              — list all families
GET    /api/families/{family_id}                  — get family
PUT    /api/families/{family_id}                  — update family
DELETE /api/families/{family_id}                  — delete family

POST   /api/families/{family_id}/members          — add member
GET    /api/families/{family_id}/members          — list members
GET    /api/families/{family_id}/members/{mid}    — get member
PUT    /api/families/{family_id}/members/{mid}    — update member
DELETE /api/families/{family_id}/members/{mid}    — delete member
"""

from __future__ import annotations

import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

import database as db
from deps import get_current_family, get_current_user
from models import (
    Family,
    FamilyCreate,
    FamilyUpdate,
    FamilyMember,
    FamilyMemberCreate,
    FamilyMemberUpdate,
    APIResponse,
    LifeStage,
    Sex,
    ActivityLevel,
    DietaryStyle,
    WellnessPhilosophy,
    DoshaType,
)
from observability import get_tracer

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = get_tracer("route.family")


def _family_to_dict(family: Family) -> dict:
    return json.loads(family.model_dump_json())


def _member_to_dict(member: FamilyMember) -> dict:
    return json.loads(member.model_dump_json())


# ---------------------------------------------------------------------------
# Family endpoints
# ---------------------------------------------------------------------------


@router.post("/families", response_model=APIResponse, status_code=201)
async def create_family(body: FamilyCreate, current_user: dict = Depends(get_current_user)):
    """Create a new family with its members. Requires auth — links family to the signed-in user."""
    with _tracer.start_as_current_span("route.family.create"):
        # Build member models
        members: list[FamilyMember] = []
        for m in body.members:
            members.append(FamilyMember(id=uuid4(), **m.model_dump()))

        family = Family(
            id=uuid4(),
            name=body.name,
            members=members,
            budget_weekly=body.budget_weekly,
            quality_preference=body.quality_preference,
            plan_frequency=body.plan_frequency,
        )

        family_dict = _family_to_dict(family)
        family_dict["auth_user_id"] = current_user["id"]
        record = await db.create_family(family_dict)

        # Persist each member separately for individual lookups
        for member in members:
            member_dict = _member_to_dict(member)
            await db.create_member(str(family.id), member_dict)

        return APIResponse(
            data=family_dict,
            message="Family created successfully.",
        )


@router.get("/families", response_model=APIResponse)
async def list_families(current_family: dict = Depends(get_current_family)):
    """Return the authenticated user's family."""
    return APIResponse(data=[current_family])


@router.get("/families/{family_id}", response_model=APIResponse)
async def get_family(family_id: str, current_family: dict = Depends(get_current_family)):
    """Return a single family by ID — must be the authenticated user's family."""
    if str(current_family["id"]) != family_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return APIResponse(data=current_family)


@router.put("/families/{family_id}", response_model=APIResponse)
async def update_family(family_id: str, body: FamilyUpdate, current_family: dict = Depends(get_current_family)):
    """Update top-level family fields."""
    if str(current_family["id"]) != family_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    with _tracer.start_as_current_span("route.family.update"):
        record = await db.get_family(family_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Family not found.")

        current: dict = dict(record).get("data", dict(record))

        update_data = body.model_dump(exclude_none=True)
        for k, v in update_data.items():
            if hasattr(v, "value"):
                update_data[k] = v.value
        current.update(update_data)

        await db.update_family(family_id, current)
        return APIResponse(data=current, message="Family updated.")


@router.delete("/families/{family_id}", response_model=APIResponse)
async def delete_family(family_id: str, current_family: dict = Depends(get_current_family)):
    """Delete the authenticated user's family."""
    if str(current_family["id"]) != family_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    with _tracer.start_as_current_span("route.family.delete"):
        await db.delete_family(family_id)
        return APIResponse(message=f"Family {family_id} deleted.")


# ---------------------------------------------------------------------------
# Member endpoints
# ---------------------------------------------------------------------------


@router.post("/families/{family_id}/members", response_model=APIResponse, status_code=201)
async def add_member(family_id: str, body: FamilyMemberCreate, current_family: dict = Depends(get_current_family)):
    """Add a new member to the authenticated user's family."""
    if str(current_family["id"]) != family_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    with _tracer.start_as_current_span("route.family.add_member"):
        fam_record = await db.get_family(family_id)
        if fam_record is None:
            raise HTTPException(status_code=404, detail="Family not found.")

        member = FamilyMember(id=uuid4(), **body.model_dump())
        member_dict = _member_to_dict(member)
        await db.create_member(family_id, member_dict)

        # Also update the members list in the family data blob
        family_data: dict = dict(fam_record).get("data", dict(fam_record))
        members_list: list = family_data.get("members", [])
        members_list.append(member_dict)
        family_data["members"] = members_list
        await db.update_family(family_id, family_data)

        return APIResponse(data=member_dict, message="Member added.")


@router.get("/families/{family_id}/members", response_model=APIResponse)
async def list_members(family_id: str, current_family: dict = Depends(get_current_family)):
    """List all members of the authenticated user's family."""
    if str(current_family["id"]) != family_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    with _tracer.start_as_current_span("route.family.list_members"):
        records = await db.get_family_members(family_id)
        data = [dict(r).get("data", dict(r)) for r in records]
        return APIResponse(data=data)


@router.get("/families/{family_id}/members/{member_id}", response_model=APIResponse)
async def get_member(family_id: str, member_id: str, current_family: dict = Depends(get_current_family)):
    """Get a single family member — must belong to the authenticated user's family."""
    if str(current_family["id"]) != family_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    with _tracer.start_as_current_span("route.family.get_member"):
        record = await db.get_member(member_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Member not found.")
        return APIResponse(data=dict(record).get("data", dict(record)))


@router.put("/families/{family_id}/members/{member_id}", response_model=APIResponse)
async def update_member(family_id: str, member_id: str, body: FamilyMemberUpdate, current_family: dict = Depends(get_current_family)):
    """Update a family member's profile."""
    if str(current_family["id"]) != family_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    with _tracer.start_as_current_span("route.family.update_member"):
        record = await db.get_member(member_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Member not found.")

        current: dict = dict(record).get("data", dict(record))
        update_data = body.model_dump(exclude_none=True)

        # Serialize enum values
        for k, v in update_data.items():
            if hasattr(v, "value"):
                update_data[k] = v.value
            elif isinstance(v, list):
                update_data[k] = [
                    item.value if hasattr(item, "value") else item for item in v
                ]

        current.update(update_data)
        await db.update_member(member_id, current)

        # Sync back to family data blob
        fam_record = await db.get_family(family_id)
        if fam_record:
            family_data: dict = dict(fam_record).get("data", dict(fam_record))
            members_list: list[dict] = family_data.get("members", [])
            for i, m in enumerate(members_list):
                if str(m.get("id")) == member_id:
                    members_list[i] = current
                    break
            family_data["members"] = members_list
            await db.update_family(family_id, family_data)

        return APIResponse(data=current, message="Member updated.")


@router.delete("/families/{family_id}/members/{member_id}", response_model=APIResponse)
async def delete_member(family_id: str, member_id: str, current_family: dict = Depends(get_current_family)):
    """Remove a member from the authenticated user's family."""
    if str(current_family["id"]) != family_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    with _tracer.start_as_current_span("route.family.delete_member"):
        record = await db.get_member(member_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Member not found.")

        await db.delete_member(member_id)

        # Remove from family data blob
        fam_record = await db.get_family(family_id)
        if fam_record:
            family_data: dict = dict(fam_record).get("data", dict(fam_record))
            family_data["members"] = [
                m for m in family_data.get("members", [])
                if str(m.get("id")) != member_id
            ]
            await db.update_family(family_id, family_data)

        return APIResponse(message=f"Member {member_id} deleted.")
