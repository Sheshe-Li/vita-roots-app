"""
Approval routes — Human-in-the-Loop (HITL)
Handles plan and grocery list approval requests and token-based resolution.

POST   /api/approvals/plan                    — create plan approval request
GET    /api/approvals/plan/{token}/approve    — approve plan via email link
GET    /api/approvals/plan/{token}/reject     — reject plan via email link
GET    /api/approvals/plan/pending/{fid}      — list pending plan approvals

POST   /api/approvals/grocery                    — create grocery approval request
GET    /api/approvals/grocery/{token}/approve    — approve grocery list via email link
GET    /api/approvals/grocery/{token}/reject     — reject grocery list via email link
GET    /api/approvals/grocery/pending/{fid}      — list pending grocery approvals
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import database as db
import email_service as email
from models import APIResponse
from observability import get_tracer

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = get_tracer("route.approvals")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class PlanApprovalRequest(BaseModel):
    family_id: str
    meal_plan_id: str


class GroceryApprovalRequest(BaseModel):
    family_id: str
    grocery_list_id: str


# ---------------------------------------------------------------------------
# Plan approval endpoints
# ---------------------------------------------------------------------------


@router.post("/approvals/plan", response_model=APIResponse, status_code=201)
async def request_plan_approval(body: PlanApprovalRequest):
    """
    Create a pending plan approval and notify the family via email and in-app alert.
    Called automatically by the WellnessAgent after generating a meal plan.
    """
    with _tracer.start_as_current_span("route.approvals.plan.create"):
        # Verify family exists
        family = await db.get_family(body.family_id)
        if not family:
            raise HTTPException(status_code=404, detail="Family not found.")

        # Verify meal plan exists
        plan = await db.get_meal_plan(body.meal_plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Meal plan not found.")

        # Create approval record
        approval = await db.create_plan_approval(body.family_id, body.meal_plan_id)
        if not approval:
            raise HTTPException(status_code=500, detail="Failed to create approval record.")

        token = str(approval["token"])
        week_start = str(plan.get("week_start", "this week"))

        # Send email notification if family has email and notifications enabled
        email_sent = False
        if family.get("email") and family.get("notify_email", True):
            email_sent = await email.send_plan_approval_email(
                to_email=family["email"],
                family_name=family["name"],
                client_number=family["client_number"],
                token=token,
                week_start=week_start,
            )
            if email_sent:
                await db.execute(
                    "UPDATE plan_approvals SET email_sent = true, email_sent_at = NOW() WHERE token = $1",
                    token,
                ) if hasattr(db, 'execute') else None

        # Log action for audit trail
        await db.log_action(
            action="plan_approval_requested",
            family_id=body.family_id,
            entity_type="meal_plan",
            entity_id=body.meal_plan_id,
            details={
                "token": token,
                "week_start": week_start,
                "email_sent": email_sent,
            },
        )

        return APIResponse(
            data={
                "approval_id": str(approval["id"]),
                "token": token,
                "status": "pending",
                "email_sent": email_sent,
                "family_id": body.family_id,
                "meal_plan_id": body.meal_plan_id,
            },
            message="Plan approval request created. Family has been notified.",
        )


@router.get("/approvals/plan/{token}/approve", response_class=HTMLResponse)
async def approve_plan(token: str):
    """
    Approve a meal plan via email link. Returns a confirmation HTML page.
    This endpoint is called when the family clicks 'Approve' in their email.
    """
    with _tracer.start_as_current_span("route.approvals.plan.approve"):
        approval = await db.get_plan_approval_by_token(token)

        if not approval:
            return _result_page("Invalid Link", "This approval link is invalid or has already been used.", success=False)

        if approval["status"] != "pending":
            return _result_page(
                "Already Decided",
                f"This plan was already {approval['status']}. No further action needed.",
                success=approval["status"] == "approved",
            )

        result = await db.resolve_plan_approval(token, "approved")
        if not result:
            return _result_page("Error", "Something went wrong. Please contact support.", success=False)

        # Approve the meal plan itself
        await db.approve_meal_plan(str(approval["meal_plan_id"]))

        # Send confirmation email
        family = await db.get_family(str(approval["family_id"]))
        if family and family.get("email"):
            await email.send_approval_confirmation_email(
                to_email=family["email"],
                family_name=family["name"],
                approval_type="plan",
                decision="approved",
            )

        await db.log_action(
            action="plan_approved",
            family_id=str(approval["family_id"]),
            entity_type="meal_plan",
            entity_id=str(approval["meal_plan_id"]),
            details={"token": token, "method": "email_link"},
        )

        return _result_page(
            "Meal Plan Approved ✓",
            "Your meal plan has been approved. Your wellness journey continues!",
            success=True,
        )


@router.get("/approvals/plan/{token}/reject", response_class=HTMLResponse)
async def reject_plan(token: str):
    """
    Reject a meal plan via email link. Returns a confirmation HTML page.
    """
    with _tracer.start_as_current_span("route.approvals.plan.reject"):
        approval = await db.get_plan_approval_by_token(token)

        if not approval:
            return _result_page("Invalid Link", "This approval link is invalid or has already been used.", success=False)

        if approval["status"] != "pending":
            return _result_page(
                "Already Decided",
                f"This plan was already {approval['status']}. No further action needed.",
                success=approval["status"] == "approved",
            )

        result = await db.resolve_plan_approval(token, "rejected")
        if not result:
            return _result_page("Error", "Something went wrong. Please contact support.", success=False)

        family = await db.get_family(str(approval["family_id"]))
        if family and family.get("email"):
            await email.send_approval_confirmation_email(
                to_email=family["email"],
                family_name=family["name"],
                approval_type="plan",
                decision="rejected",
            )

        await db.log_action(
            action="plan_rejected",
            family_id=str(approval["family_id"]),
            entity_type="meal_plan",
            entity_id=str(approval["meal_plan_id"]),
            details={"token": token, "method": "email_link"},
        )

        return _result_page(
            "Meal Plan Rejected",
            "Your meal plan has been rejected. Your wellness agent will generate a revised plan.",
            success=False,
        )


@router.get("/approvals/plan/pending/{family_id}", response_model=APIResponse)
async def get_pending_plan_approvals(family_id: str):
    """Return all pending plan approvals for a family. Used by the dashboard."""
    with _tracer.start_as_current_span("route.approvals.plan.pending"):
        approvals = await db.get_pending_plan_approvals(family_id)
        return APIResponse(data=approvals)


# ---------------------------------------------------------------------------
# In-app approval endpoints (for dashboard buttons)
# ---------------------------------------------------------------------------


@router.post("/approvals/plan/{token}/decide", response_model=APIResponse)
async def decide_plan_inapp(token: str, decision: str):
    """
    Resolve a plan approval from the in-app dashboard.
    decision must be 'approved' or 'rejected'.
    """
    with _tracer.start_as_current_span("route.approvals.plan.decide_inapp"):
        if decision not in ("approved", "rejected"):
            raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")

        approval = await db.get_plan_approval_by_token(token)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found.")
        if approval["status"] != "pending":
            raise HTTPException(status_code=409, detail=f"Approval already {approval['status']}.")

        await db.resolve_plan_approval(token, decision)

        if decision == "approved":
            await db.approve_meal_plan(str(approval["meal_plan_id"]))

        await db.log_action(
            action=f"plan_{decision}",
            family_id=str(approval["family_id"]),
            entity_type="meal_plan",
            entity_id=str(approval["meal_plan_id"]),
            details={"token": token, "method": "in_app"},
        )

        return APIResponse(
            data={"token": token, "decision": decision},
            message=f"Meal plan {decision}.",
        )


# ---------------------------------------------------------------------------
# Grocery approval endpoints
# ---------------------------------------------------------------------------


@router.post("/approvals/grocery", response_model=APIResponse, status_code=201)
async def request_grocery_approval(body: GroceryApprovalRequest):
    """
    Create a pending grocery approval and notify the family.
    Called automatically after a grocery list is generated.
    """
    with _tracer.start_as_current_span("route.approvals.grocery.create"):
        family = await db.get_family(body.family_id)
        if not family:
            raise HTTPException(status_code=404, detail="Family not found.")

        grocery_list = await db.get_grocery_list(body.grocery_list_id)
        if not grocery_list:
            raise HTTPException(status_code=404, detail="Grocery list not found.")

        approval = await db.create_grocery_approval(body.family_id, body.grocery_list_id)
        if not approval:
            raise HTTPException(status_code=500, detail="Failed to create approval record.")

        token = str(approval["token"])
        items = grocery_list.get("items_json", [])
        item_count = len(items) if isinstance(items, list) else 0
        total_cost = float(grocery_list.get("total_estimated_cost", 0))

        email_sent = False
        if family.get("email") and family.get("notify_email", True):
            email_sent = await email.send_grocery_approval_email(
                to_email=family["email"],
                family_name=family["name"],
                client_number=family["client_number"],
                token=token,
                total_cost=total_cost,
                item_count=item_count,
            )

        await db.log_action(
            action="grocery_approval_requested",
            family_id=body.family_id,
            entity_type="grocery_list",
            entity_id=body.grocery_list_id,
            details={
                "token": token,
                "item_count": item_count,
                "total_cost": total_cost,
                "email_sent": email_sent,
            },
        )

        return APIResponse(
            data={
                "approval_id": str(approval["id"]),
                "token": token,
                "status": "pending",
                "email_sent": email_sent,
                "item_count": item_count,
                "total_cost": total_cost,
            },
            message="Grocery approval request created. Family has been notified.",
        )


@router.get("/approvals/grocery/{token}/approve", response_class=HTMLResponse)
async def approve_grocery(token: str):
    """Approve a grocery list via email link."""
    with _tracer.start_as_current_span("route.approvals.grocery.approve"):
        approval = await db.get_grocery_approval_by_token(token)

        if not approval:
            return _result_page("Invalid Link", "This approval link is invalid or has already been used.", success=False)

        if approval["status"] != "pending":
            return _result_page(
                "Already Decided",
                f"This grocery list was already {approval['status']}.",
                success=approval["status"] == "approved",
            )

        await db.resolve_grocery_approval(token, "approved")
        await db.approve_grocery_list(str(approval["grocery_list_id"]))

        family = await db.get_family(str(approval["family_id"]))
        if family and family.get("email"):
            await email.send_approval_confirmation_email(
                to_email=family["email"],
                family_name=family["name"],
                approval_type="grocery",
                decision="approved",
            )

        await db.log_action(
            action="grocery_approved",
            family_id=str(approval["family_id"]),
            entity_type="grocery_list",
            entity_id=str(approval["grocery_list_id"]),
            details={"token": token, "method": "email_link"},
        )

        return _result_page(
            "Grocery List Approved ✓",
            "Your grocery list has been approved. Happy shopping!",
            success=True,
        )


@router.get("/approvals/grocery/{token}/reject", response_class=HTMLResponse)
async def reject_grocery(token: str):
    """Reject a grocery list via email link."""
    with _tracer.start_as_current_span("route.approvals.grocery.reject"):
        approval = await db.get_grocery_approval_by_token(token)

        if not approval:
            return _result_page("Invalid Link", "This approval link is invalid or has already been used.", success=False)

        if approval["status"] != "pending":
            return _result_page(
                "Already Decided",
                f"This grocery list was already {approval['status']}.",
                success=approval["status"] == "approved",
            )

        await db.resolve_grocery_approval(token, "rejected")

        family = await db.get_family(str(approval["family_id"]))
        if family and family.get("email"):
            await email.send_approval_confirmation_email(
                to_email=family["email"],
                family_name=family["name"],
                approval_type="grocery",
                decision="rejected",
            )

        await db.log_action(
            action="grocery_rejected",
            family_id=str(approval["family_id"]),
            entity_type="grocery_list",
            entity_id=str(approval["grocery_list_id"]),
            details={"token": token, "method": "email_link"},
        )

        return _result_page(
            "Grocery List Rejected",
            "Your grocery list has been rejected. Your wellness agent can generate a revised list.",
            success=False,
        )


@router.get("/approvals/grocery/pending/{family_id}", response_model=APIResponse)
async def get_pending_grocery_approvals(family_id: str):
    """Return all pending grocery approvals for a family."""
    with _tracer.start_as_current_span("route.approvals.grocery.pending"):
        approvals = await db.get_pending_grocery_approvals(family_id)
        return APIResponse(data=approvals)


@router.post("/approvals/grocery/{token}/decide", response_model=APIResponse)
async def decide_grocery_inapp(token: str, decision: str):
    """Resolve a grocery approval from the in-app dashboard."""
    with _tracer.start_as_current_span("route.approvals.grocery.decide_inapp"):
        if decision not in ("approved", "rejected"):
            raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")

        approval = await db.get_grocery_approval_by_token(token)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found.")
        if approval["status"] != "pending":
            raise HTTPException(status_code=409, detail=f"Approval already {approval['status']}.")

        await db.resolve_grocery_approval(token, decision)

        if decision == "approved":
            await db.approve_grocery_list(str(approval["grocery_list_id"]))

        await db.log_action(
            action=f"grocery_{decision}",
            family_id=str(approval["family_id"]),
            entity_type="grocery_list",
            entity_id=str(approval["grocery_list_id"]),
            details={"token": token, "method": "in_app"},
        )

        return APIResponse(
            data={"token": token, "decision": decision},
            message=f"Grocery list {decision}.",
        )


# ---------------------------------------------------------------------------
# HTML response helper
# ---------------------------------------------------------------------------


def _result_page(title: str, message: str, success: bool = True) -> str:
    color = "#2d6a4f" if success else "#c0392b"
    icon = "✓" if success else "✗"
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>{title} — Vita Roots</title>
      <style>
        body {{ font-family: sans-serif; display: flex; align-items: center; justify-content: center;
                min-height: 100vh; margin: 0; background: #f8f9fa; }}
        .card {{ background: white; border-radius: 12px; padding: 48px; max-width: 480px;
                 text-align: center; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
        .icon {{ font-size: 48px; margin-bottom: 16px; }}
        h1 {{ color: {color}; font-size: 24px; margin: 0 0 16px; }}
        p {{ color: #555; line-height: 1.6; }}
        .brand {{ color: #aaa; font-size: 13px; margin-top: 32px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="icon">{icon}</div>
        <h1>{title}</h1>
        <p>{message}</p>
        <p class="brand">Vita Roots Family Wellness</p>
      </div>
    </body>
    </html>
    """
