"""
Meal plan routes.
POST   /api/meal-plans/generate       — generate and save a meal plan
GET    /api/meal-plans/{plan_id}      — retrieve a saved plan
POST   /api/meals/{meal_id}/swap      — get an AI alternative for a meal
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_family

from agent import WellnessAgent
from database import (
    get_family,
    get_meal_plan,
    get_family_members,
    save_meal_plan,
)
from models import (
    Family,
    FamilyMember,
    MealPlan,
    MealPlanRequest,
    MealSwapRequest,
    APIResponse,
    DayMeals,
    Meal,
    Ingredient,
)
from observability import get_tracer, add_wellness_attributes

logger = logging.getLogger(__name__)
router = APIRouter()
_agent = WellnessAgent()
_tracer = get_tracer("route.meal_plans")


def _family_from_record(record: dict) -> Family:
    data = record.get("data", record)
    return Family.model_validate(data)


def _build_meal_plan_from_agent_data(
    family_id: str,
    week_start: str,
    agent_data: dict,
) -> MealPlan:
    """Map raw agent tool-use output into a MealPlan Pydantic model."""
    days_out: list[DayMeals] = []
    for raw_day in agent_data.get("days", []):
        def _parse_meal(raw: dict | None) -> Meal | None:
            if not raw:
                return None
            ingredients = [
                Ingredient(
                    name=i.get("name", ""),
                    quantity=i.get("quantity", ""),
                    unit=i.get("unit", ""),
                    notes=i.get("notes"),
                )
                for i in raw.get("ingredients", [])
            ]
            return Meal(
                id=uuid4(),
                name=raw.get("name", ""),
                ingredients=ingredients,
                instructions=raw.get("instructions", []),
                prep_time=raw.get("prep_time", 0),
                cook_time=raw.get("cook_time", 0),
                why_it_works=raw.get("why_it_works", {}),
                member_compatibility=raw.get("member_compatibility", []),
                cuisine_type=raw.get("cuisine_type"),
                tags=raw.get("tags", []),
            )

        snacks = [
            m for m in [_parse_meal(s) for s in raw_day.get("snacks", [])]
            if m is not None
        ]

        days_out.append(
            DayMeals(
                day=raw_day.get("day", ""),
                breakfast=_parse_meal(raw_day.get("breakfast")),
                lunch=_parse_meal(raw_day.get("lunch")),
                dinner=_parse_meal(raw_day.get("dinner")),
                snacks=snacks,
            )
        )

    return MealPlan(
        id=uuid4(),
        family_id=family_id,  # type: ignore[arg-type]
        week_start=week_start,
        days=days_out,
        notes=agent_data.get("notes"),
        created_at=datetime.utcnow().isoformat(),
    )


@router.post("/meal-plans/generate", response_model=APIResponse)
async def generate_meal_plan(request: MealPlanRequest, current_family: dict = Depends(get_current_family)):
    """Generate a 7-day meal plan for the family and persist it."""
    family_id = str(current_family["id"])
    with _tracer.start_as_current_span("route.meal_plans.generate") as span:
        add_wellness_attributes(span, family_id=family_id, request_type="meal_plan")

        db_record = await get_family(family_id)
        if db_record is None:
            raise HTTPException(status_code=404, detail="Family not found.")

        family = _family_from_record(dict(db_record))

        try:
            agent_data = await _agent.generate_meal_plan(
                family=family,
                week_start=request.week_start,
                special_notes=request.special_notes or "",
            )
        except Exception as exc:
            logger.exception("Meal plan generation failed")
            raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

        meal_plan = _build_meal_plan_from_agent_data(
            family_id=family_id,
            week_start=request.week_start,
            agent_data=agent_data,
        )

        # Persist to database
        plan_dict = json.loads(meal_plan.model_dump_json())
        await save_meal_plan(plan_dict)

        return APIResponse(data=plan_dict, message="Meal plan generated successfully.")


@router.get("/meal-plans/{plan_id}", response_model=APIResponse)
async def get_meal_plan_endpoint(plan_id: str, _: dict = Depends(get_current_family)):
    """Retrieve a previously saved meal plan."""
    with _tracer.start_as_current_span("route.meal_plans.get") as span:
        span.set_attribute("meal_plan.id", plan_id)

        record = await get_meal_plan(plan_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Meal plan not found.")

        return APIResponse(data=dict(record).get("data", dict(record)))


@router.post("/meals/{meal_id}/swap", response_model=APIResponse)
async def swap_meal(meal_id: str, request: MealSwapRequest, current_family: dict = Depends(get_current_family)):
    """Get an AI-generated alternative for a specific meal."""
    family_id = str(current_family["id"])
    with _tracer.start_as_current_span("route.meal_plans.swap") as span:
        add_wellness_attributes(span, family_id=family_id, request_type="meal_plan")
        span.set_attribute("meal.id", meal_id)

        db_record = await get_family(family_id)
        if db_record is None:
            raise HTTPException(status_code=404, detail="Family not found.")

        family = _family_from_record(dict(db_record))

        try:
            alternative = await _agent.swap_meal(
                family=family,
                meal_name=meal_id,
                reason=request.reason or "",
            )
        except Exception as exc:
            logger.exception("Meal swap failed")
            raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

        return APIResponse(data=alternative, message="Alternative meal generated.")
