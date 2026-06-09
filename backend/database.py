"""
Database layer — Supabase Python client (REST over HTTPS).
Uses supabase-py which communicates over HTTPS — no direct Postgres port needed.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
logger = logging.getLogger(__name__)

_client: Optional[Client] = None


# ---------------------------------------------------------------------------
# Client management
# ---------------------------------------------------------------------------


def get_client() -> Optional[Client]:
    global _client
    if _client is None:
        _client = _create_client()
    return _client


def _create_client() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

    if not url or not key:
        logger.warning("No Supabase URL or key configured. Running without persistent storage.")
        return None

    try:
        client = create_client(url, key)
        logger.info("Supabase client created successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


def is_connected() -> bool:
    return get_client() is not None


# ---------------------------------------------------------------------------
# Families
# ---------------------------------------------------------------------------


async def create_family(data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("families").insert({
            "id": str(data["id"]),
            "name": data["name"],
            "email": data.get("email", ""),
            "phone": data.get("phone"),
            "budget_weekly": float(data["budget_weekly"]),
            "quality_preference": data.get("quality_preference", "whole_foods"),
            "plan_frequency": data.get("plan_frequency", "weekly"),
            "notify_email": data.get("notify_email", True),
            "notify_inapp": data.get("notify_inapp", True),
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"create_family error: {e}")
        return None


async def get_family(family_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("families").select("*").eq("id", family_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_family error: {e}")
        return None


async def get_family_with_members(family_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("families").select("*, family_members(*)").eq("id", family_id).execute()
        if not result.data:
            return None
        row = result.data[0]
        row["members"] = row.pop("family_members", [])
        return row
    except Exception as e:
        logger.error(f"get_family_with_members error: {e}")
        return None


async def get_family_by_client_number(client_number: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("families").select("*").eq("client_number", client_number).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_family_by_client_number error: {e}")
        return None


async def update_family(family_id: str, data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        update_data = {k: v for k, v in {
            "name": data.get("name"),
            "budget_weekly": float(data["budget_weekly"]) if "budget_weekly" in data else None,
            "quality_preference": data.get("quality_preference"),
            "plan_frequency": data.get("plan_frequency"),
            "notify_email": data.get("notify_email"),
            "notify_inapp": data.get("notify_inapp"),
        }.items() if v is not None}
        result = client.table("families").update(update_data).eq("id", family_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"update_family error: {e}")
        return None


async def delete_family(family_id: str) -> bool:
    client = get_client()
    if not client:
        return False
    try:
        client.table("families").delete().eq("id", family_id).execute()
        return True
    except Exception as e:
        logger.error(f"delete_family error: {e}")
        return False


async def list_families() -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("families").select("*").order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"list_families error: {e}")
        return []


# ---------------------------------------------------------------------------
# Family Members
# ---------------------------------------------------------------------------


async def create_member(family_id: str, data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("family_members").insert({
            "id": str(data["id"]),
            "family_id": family_id,
            "name": data["name"],
            "age": int(data["age"]),
            "life_stage": data.get("life_stage", "adult"),
            "sex": data.get("sex", "prefer_not_to_say"),
            "activity_level": data.get("activity_level", "moderately_active"),
            "dietary_style": data.get("dietary_style", "omnivore"),
            "wellness_philosophy": data.get("wellness_philosophy", "no_preference"),
            "dosha": data.get("dosha", "unknown"),
            "goals": data.get("goals", []),
            "allergies": data.get("allergies", []),
            "dislikes": data.get("dislikes", []),
            "loves": data.get("loves", []),
            "cuisine_prefs": data.get("cuisine_prefs", []),
            "health_conditions": data.get("health_conditions", []),
            "current_supplements": data.get("current_supplements", []),
            "supplements_open": data.get("supplements_open", True),
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"create_member error: {e}")
        return None


async def get_member(member_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("family_members").select("*").eq("id", member_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_member error: {e}")
        return None


async def get_member_by_number(member_number: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("family_members").select("*").eq("member_number", member_number).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_member_by_number error: {e}")
        return None


async def get_family_members(family_id: str) -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("family_members").select("*").eq("family_id", family_id).order("created_at").execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_family_members error: {e}")
        return []


async def update_member(member_id: str, data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        update_data = {k: v for k, v in data.items() if v is not None and k != "id"}
        result = client.table("family_members").update(update_data).eq("id", member_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"update_member error: {e}")
        return None


async def delete_member(member_id: str) -> bool:
    client = get_client()
    if not client:
        return False
    try:
        client.table("family_members").delete().eq("id", member_id).execute()
        return True
    except Exception as e:
        logger.error(f"delete_member error: {e}")
        return False


# ---------------------------------------------------------------------------
# Meal Plans
# ---------------------------------------------------------------------------


async def save_meal_plan(data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("meal_plans").insert({
            "id": str(data["id"]),
            "family_id": str(data["family_id"]),
            "week_start": data["week_start"],
            "days_json": data.get("days", []),
            "notes": data.get("notes"),
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"save_meal_plan error: {e}")
        return None


async def create_meal_plan(
    family_id: str,
    week_start: str,
    days_json: list,
    notes: str = None,
) -> Optional[str]:
    client = get_client()
    if not client:
        return None
    try:
        plan_id = str(uuid.uuid4())
        result = client.table("meal_plans").insert({
            "id": plan_id,
            "family_id": family_id,
            "week_start": week_start,
            "days_json": days_json,
            "notes": notes,
        }).execute()
        return result.data[0].get("id", plan_id) if result.data else plan_id
    except Exception as e:
        logger.error(f"create_meal_plan error: {e}")
        return None


async def get_meal_plan(plan_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("meal_plans").select("*").eq("id", plan_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_meal_plan error: {e}")
        return None


async def get_family_meal_plans(family_id: str) -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("meal_plans").select("*").eq("family_id", family_id).order("week_start", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_family_meal_plans error: {e}")
        return []


async def approve_meal_plan(plan_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("meal_plans").update({
            "approved": True,
        }).eq("id", plan_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"approve_meal_plan error: {e}")
        return None


# ---------------------------------------------------------------------------
# Grocery Lists
# ---------------------------------------------------------------------------


async def save_grocery_list(data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("grocery_lists").insert({
            "id": str(data["id"]),
            "family_id": str(data["family_id"]),
            "meal_plan_id": str(data["meal_plan_id"]),
            "items_json": data.get("items", []),
            "total_estimated_cost": float(data.get("total_estimated_cost", 0)),
            "budget_weekly": float(data.get("budget_weekly", 0)),
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"save_grocery_list error: {e}")
        return None


async def get_grocery_list(list_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("grocery_lists").select("*").eq("id", list_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_grocery_list error: {e}")
        return None


async def get_grocery_list_by_plan(plan_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("grocery_lists").select("*").eq("meal_plan_id", plan_id).order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_grocery_list_by_plan error: {e}")
        return None


async def update_grocery_list_data(list_id: str, data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("grocery_lists").update({
            "items_json": data.get("items", []),
            "total_estimated_cost": float(data.get("total_estimated_cost", 0)),
        }).eq("id", list_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"update_grocery_list_data error: {e}")
        return None


async def approve_grocery_list(list_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("grocery_lists").update({
            "approved": True,
        }).eq("id", list_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"approve_grocery_list error: {e}")
        return None


# ---------------------------------------------------------------------------
# Supplement Guides
# ---------------------------------------------------------------------------


async def save_supplement_guide(data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("supplement_guides").insert({
            "id": str(data["id"]),
            "family_id": str(data["family_id"]),
            "member_id": str(data["member_id"]),
            "recommendations": data.get("recommendations", []),
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"save_supplement_guide error: {e}")
        return None


async def get_supplement_guide(member_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("supplement_guides").select("*").eq("member_id", member_id).order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_supplement_guide error: {e}")
        return None


# ---------------------------------------------------------------------------
# Plan Approvals (HITL)
# ---------------------------------------------------------------------------


async def create_plan_approval(family_id: str, meal_plan_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("plan_approvals").insert({
            "family_id": family_id,
            "meal_plan_id": meal_plan_id,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"create_plan_approval error: {e}")
        return None


async def get_plan_approval_by_token(token: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("plan_approvals").select("*").eq("token", token).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_plan_approval_by_token error: {e}")
        return None


async def resolve_plan_approval(token: str, status: str, notes: str = None) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("plan_approvals").update({
            "status": status,
            "notes": notes,
        }).eq("token", token).eq("status", "pending").execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"resolve_plan_approval error: {e}")
        return None


async def get_pending_plan_approvals(family_id: str) -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("plan_approvals").select("*").eq("family_id", family_id).eq("status", "pending").order("requested_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_pending_plan_approvals error: {e}")
        return []


# ---------------------------------------------------------------------------
# Grocery Approvals (HITL)
# ---------------------------------------------------------------------------


async def create_grocery_approval(family_id: str, grocery_list_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("grocery_approvals").insert({
            "family_id": family_id,
            "grocery_list_id": grocery_list_id,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"create_grocery_approval error: {e}")
        return None


async def get_grocery_approval_by_token(token: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("grocery_approvals").select("*").eq("token", token).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_grocery_approval_by_token error: {e}")
        return None


async def resolve_grocery_approval(token: str, status: str, notes: str = None) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("grocery_approvals").update({
            "status": status,
            "notes": notes,
        }).eq("token", token).eq("status", "pending").execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"resolve_grocery_approval error: {e}")
        return None


async def get_pending_grocery_approvals(family_id: str) -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("grocery_approvals").select("*").eq("family_id", family_id).eq("status", "pending").order("requested_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_pending_grocery_approvals error: {e}")
        return []


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


async def create_signal(
    signal_type: str,
    title: str,
    summary: str = None,
    source_name: str = None,
    score: int = 0,
    status: str = "pending",
    metadata: dict = None,
) -> Optional[str]:
    client = get_client()
    if not client:
        return None
    try:
        signal_id = str(uuid.uuid4())
        result = client.table("signals").insert({
            "id": signal_id,
            "signal_type": signal_type,
            "title": title,
            "summary": summary,
            "source_name": source_name,
            "score": int(score),
            "status": status,
            "metadata": metadata or {},
        }).execute()
        return result.data[0].get("id", signal_id) if result.data else signal_id
    except Exception as e:
        logger.error(f"create_signal error: {e}")
        return None


async def update_signal_status(signal_id: str, status: str, score: int = None) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        update_data = {"status": status}
        if score is not None:
            update_data["score"] = score
        result = client.table("signals").update(update_data).eq("id", signal_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"update_signal_status error: {e}")
        return None


async def get_pending_signals() -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("signals").select("*").eq("status", "pending").order("caught_at").execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_pending_signals error: {e}")
        return []


# ---------------------------------------------------------------------------
# Signal Alerts
# ---------------------------------------------------------------------------


async def create_signal_alert(
    family_id: str,
    signal_id: str = None,
    signal_type: str = None,
    title: str = None,
    summary: str = None,
    score: int = 0,
    matched_members: list = None,
    new_plan_id: str = None,
) -> Optional[str]:
    client = get_client()
    if not client:
        return None
    try:
        alert_id = str(uuid.uuid4())
        result = client.table("signal_alerts").insert({
            "id": alert_id,
            "family_id": family_id,
            "signal_id": signal_id,
            "matched_members": matched_members or [],
            "new_plan_id": new_plan_id,
            "status": "pending",
        }).execute()
        return result.data[0].get("id", alert_id) if result.data else alert_id
    except Exception as e:
        logger.error(f"create_signal_alert error: {e}")
        return None


async def resolve_signal_alert(alert_id: str, decision: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("signal_alerts").update({
            "decision": decision,
        }).eq("id", alert_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"resolve_signal_alert error: {e}")
        return None


async def get_family_alerts(family_id: str) -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("signal_alerts").select("*, signals(type, title, summary, score)").eq("family_id", family_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_family_alerts error: {e}")
        return []


# ---------------------------------------------------------------------------
# Support Tickets
# ---------------------------------------------------------------------------


async def create_support_ticket(data: dict[str, Any]) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("support_tickets").insert({
            "family_id": data.get("family_id"),
            "client_number": data.get("client_number"),
            "category": data.get("category", "general"),
            "subject": data["subject"],
            "priority": data.get("priority", "normal"),
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"create_support_ticket error: {e}")
        return None


async def get_support_ticket(ticket_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("support_tickets").select("*").eq("id", ticket_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_support_ticket error: {e}")
        return None


async def get_family_tickets(family_id: str) -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("support_tickets").select("*").eq("family_id", family_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_family_tickets error: {e}")
        return []


async def update_ticket_status(ticket_id: str, status: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("support_tickets").update({"status": status}).eq("id", ticket_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"update_ticket_status error: {e}")
        return None


async def add_support_message(ticket_id: str, role: str, content: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("support_messages").insert({
            "ticket_id": ticket_id,
            "role": role,
            "content": content,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"add_support_message error: {e}")
        return None


async def get_ticket_messages(ticket_id: str) -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("support_messages").select("*").eq("ticket_id", ticket_id).order("created_at").execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_ticket_messages error: {e}")
        return []


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------


async def get_subscription_plans() -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("subscription_plans").select("*").eq("is_active", True).order("price_monthly").execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_subscription_plans error: {e}")
        return []


async def get_family_subscription(family_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("family_subscriptions").select("*, subscription_plans(name, display_name, price_monthly, features)").eq("family_id", family_id).order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_family_subscription error: {e}")
        return None


async def create_family_subscription(family_id: str, plan_id: str) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("family_subscriptions").insert({
            "family_id": family_id,
            "plan_id": plan_id,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"create_family_subscription error: {e}")
        return None


async def get_billing_history(family_id: str) -> list[dict]:
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("billing_history").select("*").eq("family_id", family_id).order("paid_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_billing_history error: {e}")
        return []


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------


async def log_action(
    action: str,
    family_id: str = None,
    member_id: str = None,
    entity_type: str = None,
    entity_id: str = None,
    details: dict = None,
) -> None:
    client = get_client()
    if not client:
        return
    try:
        client.table("audit_log").insert({
            "family_id": family_id,
            "member_id": member_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
        }).execute()
    except Exception as e:
        logger.error(f"log_action error: {e}")
