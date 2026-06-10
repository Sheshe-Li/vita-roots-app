"""
Grocery list routes.
POST  /api/grocery-lists/generate           — generate from a meal plan
GET   /api/grocery-lists/{plan_id}          — get list for a meal plan
PATCH /api/grocery-items/{item_id}/check    — toggle item checked state
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
    get_meal_plan,
    save_grocery_list,
    get_grocery_list_by_plan,
    get_grocery_list,
    update_grocery_list_data,
)
from models import (
    Family,
    GroceryList,
    GroceryItem,
    GroceryListRequest,
    GroceryItemCheckRequest,
    APIResponse,
)
from observability import get_tracer, add_wellness_attributes

logger = logging.getLogger(__name__)
router = APIRouter()
_agent = WellnessAgent()
_tracer = get_tracer("route.grocery")


def _family_from_record(record: dict) -> Family:
    data = record.get("data", record)
    return Family.model_validate(data)


def _build_grocery_list(
    family_id: str,
    meal_plan_id: str,
    budget: float,
    agent_data: dict,
) -> GroceryList:
    items = [
        GroceryItem(
            id=uuid4(),
            name=i.get("name", ""),
            quantity=float(i.get("quantity", 1)),
            unit=i.get("unit", ""),
            category=i.get("category", "other"),
            estimated_cost=float(i.get("estimated_cost", 0)),
            quality_flag=i.get("quality_flag"),
            member_tags=i.get("member_tags", []),
            money_saving_tip=i.get("money_saving_tip"),
            checked=False,
        )
        for i in agent_data.get("items", [])
    ]
    gl = GroceryList(
        id=uuid4(),
        family_id=family_id,  # type: ignore[arg-type]
        meal_plan_id=meal_plan_id,  # type: ignore[arg-type]
        items=items,
        budget_weekly=budget,
        created_at=datetime.utcnow().isoformat(),
    )
    gl.compute_total()
    return gl


@router.post("/grocery-lists/generate", response_model=APIResponse)
async def generate_grocery_list(request: GroceryListRequest, current_family: dict = Depends(get_current_family)):
    """Generate a grocery list from a meal plan."""
    family_id = str(current_family["id"])
    with _tracer.start_as_current_span("route.grocery.generate") as span:
        add_wellness_attributes(span, family_id=family_id, request_type="grocery")

        fam_record = await get_family(family_id)
        if fam_record is None:
            raise HTTPException(status_code=404, detail="Family not found.")
        family = _family_from_record(dict(fam_record))

        # Load meal plan
        plan_record = await get_meal_plan(request.meal_plan_id)
        if plan_record is None:
            raise HTTPException(status_code=404, detail="Meal plan not found.")
        meal_plan_data = dict(plan_record).get("data", {})

        try:
            agent_data = await _agent.generate_grocery_list(
                family=family,
                meal_plan_data=meal_plan_data,
                budget=request.budget,
                quality_prefs=request.quality_prefs,
            )
        except Exception as exc:
            logger.exception("Grocery list generation failed")
            raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

        grocery_list = _build_grocery_list(
            family_id=family_id,
            meal_plan_id=request.meal_plan_id,
            budget=request.budget,
            agent_data=agent_data,
        )

        gl_dict = json.loads(grocery_list.model_dump_json())
        await save_grocery_list(gl_dict)

        return APIResponse(data=gl_dict, message="Grocery list generated.")


@router.get("/grocery-lists/{plan_id}", response_model=APIResponse)
async def get_grocery_list_endpoint(plan_id: str, _: dict = Depends(get_current_family)):
    """Get the grocery list associated with a meal plan."""
    with _tracer.start_as_current_span("route.grocery.get") as span:
        span.set_attribute("meal_plan.id", plan_id)

        record = await get_grocery_list_by_plan(plan_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Grocery list not found.")

        return APIResponse(data=dict(record).get("data", dict(record)))


@router.patch("/grocery-items/{item_id}/check", response_model=APIResponse)
async def toggle_grocery_item(item_id: str, body: GroceryItemCheckRequest, _: dict = Depends(get_current_family)):
    """Toggle the checked state of a grocery list item."""
    with _tracer.start_as_current_span("route.grocery.check_item") as span:
        span.set_attribute("grocery_item.id", item_id)
        span.set_attribute("grocery_item.checked", body.checked)

        # Find the grocery list containing this item
        # We search by iterating — for production use an item-level table
        record = await get_grocery_list(item_id)  # item_id used as list lookup fallback
        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Grocery list containing item not found. Provide list ID.",
            )

        data: dict = dict(record).get("data", {})
        items: list[dict] = data.get("items", [])
        updated = False

        for item in items:
            if item.get("id") == item_id:
                item["checked"] = body.checked
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="Item not found in list.")

        data["items"] = items
        await update_grocery_list_data(str(record["id"]), data)

        return APIResponse(data={"item_id": item_id, "checked": body.checked})
