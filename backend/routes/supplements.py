"""
Supplement routes.
POST /api/supplements/generate/{member_id}  — generate guide for a member
GET  /api/supplements/{member_id}           — get saved recommendations
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_family

from agent import WellnessAgent
from database import (
    get_family,
    get_member,
    save_supplement_guide,
    get_supplement_guide,
)
from models import (
    Family,
    FamilyMember,
    SupplementGuide,
    SupplementRecommendation,
    SupplementRequest,
    APIResponse,
)
from observability import get_tracer, add_wellness_attributes

logger = logging.getLogger(__name__)
router = APIRouter()
_agent = WellnessAgent()
_tracer = get_tracer("route.supplements")


def _family_from_record(record: dict) -> Family:
    data = record.get("data", record)
    return Family.model_validate(data)


def _member_from_record(record: dict) -> FamilyMember:
    data = record.get("data", record)
    return FamilyMember.model_validate(data)


def _build_supplement_guide(
    family_id: str,
    member: FamilyMember,
    agent_data: dict,
) -> SupplementGuide:
    recommendations = [
        SupplementRecommendation(
            id=uuid4(),
            name=r.get("name", ""),
            purpose=r.get("purpose", ""),
            dose_range=r.get("dose_range", ""),
            timing=r.get("timing", ""),
            approach=r.get("approach", "general"),
            contraindication_notes=r.get("contraindication_notes"),
            form=r.get("form"),
            brand_suggestions=r.get("brand_suggestions", []),
        )
        for r in agent_data.get("recommendations", [])
    ]
    return SupplementGuide(
        id=uuid4(),
        family_id=family_id,  # type: ignore[arg-type]
        member_id=member.id,
        member_name=member.name,
        recommendations=recommendations,
        created_at=datetime.utcnow().isoformat(),
    )


@router.post("/supplements/generate/{member_id}", response_model=APIResponse)
async def generate_supplement_guide(member_id: str, request: SupplementRequest, current_family: dict = Depends(get_current_family)):
    """Generate a personalized supplement guide for a family member."""
    family_id = str(current_family["id"])
    with _tracer.start_as_current_span("route.supplements.generate") as span:
        add_wellness_attributes(span, family_id=family_id, member_id=member_id, request_type="supplement")

        fam_record = await get_family(family_id)
        if fam_record is None:
            raise HTTPException(status_code=404, detail="Family not found.")
        family = _family_from_record(dict(fam_record))

        # Load member
        mem_record = await get_member(member_id)
        if mem_record is None:
            raise HTTPException(status_code=404, detail="Family member not found.")
        member = _member_from_record(dict(mem_record))

        if not member.supplements_open:
            return APIResponse(
                data=[],
                message=f"{member.name} has not opted in for supplement guidance.",
            )

        try:
            agent_data = await _agent.generate_supplement_guide(
                family=family,
                member=member,
            )
        except Exception as exc:
            logger.exception("Supplement guide generation failed")
            raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

        guide = _build_supplement_guide(
            family_id=family_id,
            member=member,
            agent_data=agent_data,
        )

        guide_dict = json.loads(guide.model_dump_json())
        await save_supplement_guide(guide_dict)

        return APIResponse(data=guide_dict, message="Supplement guide generated.")


@router.get("/supplements/{member_id}", response_model=APIResponse)
async def get_supplement_guide_endpoint(member_id: str, _: dict = Depends(get_current_family)):
    """Get the most recent supplement guide for a family member."""
    with _tracer.start_as_current_span("route.supplements.get") as span:
        span.set_attribute("family.member_id", member_id)

        record = await get_supplement_guide(member_id)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail="No supplement guide found for this member.",
            )

        return APIResponse(data=dict(record).get("data", dict(record)))
