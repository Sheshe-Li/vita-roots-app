"""
Vita Roots — Compound Agent
Phase 2 Block 1: signal → decision → WellnessAgent action

This module is the COMPOUND layer. It sits after the SEPARATE layer (score_signal)
and decides what to do when a signal scores above the fire threshold.

Pipeline:
  score_signal returns "fire"
      → CompoundAgent.handle_fired_signal()
          → fetch family from Supabase
          → build signal-aware prompt
          → call WellnessAgent.generate_meal_plan()  (or supplement guide)
          → persist new plan to Supabase
          → create signal_alert record
          → write audit log entry
          → return CompoundResult with all trace IDs

All steps run inside a single parent Phoenix span so the full chain
shows as one trace in the Phoenix UI.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from opentelemetry import trace

import database
from agent import WellnessAgent
from models import (
    Family,
    FamilyMember,
    DietaryStyle,
    WellnessPhilosophy,
    DoshaType,
    LifeStage,
    Sex,
    ActivityLevel,
    QualityPreference,
    PlanFrequency,
)
from observability import get_tracer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class CompoundResult:
    """Returned by handle_fired_signal — contains every ID and decision for audit."""
    family_id: str
    signal_title: str
    signal_type: str
    score: int
    recommendation: str           # always "fire" when this runs
    matched_members: list[dict]
    action_taken: str             # "meal_plan_regenerated" | "supplement_updated" | "alert_only"
    new_plan_id: str | None = None
    alert_id: str | None = None
    error: str | None = None
    trace_id: str | None = None
    completed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Compound Agent
# ---------------------------------------------------------------------------

class CompoundAgent:
    """
    Orchestrates the compound action after a signal fires.
    Depends on WellnessAgent for plan generation and database for persistence.
    """

    def __init__(self) -> None:
        self._wellness = WellnessAgent()
        self._tracer = get_tracer("compound-agent")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def handle_fired_signal(
        self,
        *,
        family_id: str,
        signal_title: str,
        signal_summary: str,
        signal_type: str,            # "research" | "market"
        score: int,
        score_breakdown: list[str],
        matched_members: list[dict], # output of match_family_profiles
        signal_metadata: dict[str, Any] | None = None,
        source_name: str = "PubMed",
    ) -> CompoundResult:
        """
        Main entry point. Call this when score_signal returns recommendation="fire".

        Creates a single parent Phoenix span that contains:
          - family fetch
          - plan regeneration (child span inside WellnessAgent)
          - Supabase write
          - alert creation
          - audit log
        """
        signal_metadata = signal_metadata or {}

        with self._tracer.start_as_current_span("compound.handle_fired_signal") as span:
            # Capture trace ID for result (visible in Phoenix)
            ctx = span.get_span_context()
            trace_id = format(ctx.trace_id, "032x") if ctx else None

            span.set_attribute("signal.title", signal_title[:200])
            span.set_attribute("signal.type", signal_type)
            span.set_attribute("signal.score", score)
            span.set_attribute("signal.source", source_name)
            span.set_attribute("family.id", family_id)
            span.set_attribute("signal.matched_member_count", len(matched_members))

            try:
                # ── Step 1: Fetch family from Supabase ──────────────────
                with self._tracer.start_as_current_span("compound.fetch_family"):
                    family_data = await database.get_family_with_members(family_id)
                    if not family_data:
                        raise ValueError(f"Family {family_id} not found in Supabase")
                    family = _hydrate_family(family_data)
                    span.set_attribute("family.name", family.name)
                    span.set_attribute("family.member_count", len(family.members))

                logger.info(
                    f"[compound] Handling fired signal for {family.name} "
                    f"| score={score} | matched={len(matched_members)} members"
                )

                # ── Step 2: Build signal context note for WellnessAgent ─
                signal_note = _build_signal_note(
                    signal_title=signal_title,
                    signal_summary=signal_summary,
                    signal_type=signal_type,
                    score=score,
                    score_breakdown=score_breakdown,
                    matched_members=matched_members,
                )

                # ── Step 3: Decide action type ───────────────────────────
                # Research signals → regenerate meal plan (incorporates new evidence)
                # Market signals   → regenerate grocery list context note (price-aware)
                # Both             → always create signal_alert for HITL approval
                action_taken = (
                    "meal_plan_regenerated"
                    if signal_type == "research"
                    else "grocery_plan_flagged"
                )

                # ── Step 4: Call WellnessAgent ───────────────────────────
                with self._tracer.start_as_current_span("compound.wellness_agent_call"):
                    week_start = date.today().isoformat()
                    plan_data = await self._wellness.generate_meal_plan(
                        family=family,
                        week_start=week_start,
                        special_notes=signal_note,
                    )
                    span.set_attribute("plan.week_start", week_start)
                    span.set_attribute(
                        "plan.days_generated",
                        len(plan_data.get("days", []))
                    )

                logger.info(
                    f"[compound] WellnessAgent generated plan with "
                    f"{len(plan_data.get('days', []))} days"
                )

                # ── Step 5: Persist new meal plan to Supabase ────────────
                with self._tracer.start_as_current_span("compound.persist_plan"):
                    new_plan_id = await database.create_meal_plan(
                        family_id=family_id,
                        week_start=week_start,
                        days_json=plan_data.get("days", []),
                        notes=(
                            f"[Signal-driven regen] {signal_title[:200]}\n"
                            f"Score: {score} | Source: {source_name}"
                        ),
                    )
                    span.set_attribute("plan.id", str(new_plan_id))

                logger.info(f"[compound] New meal plan persisted: {new_plan_id}")

                # ── Step 6: Create signal record in Supabase ─────────────
                with self._tracer.start_as_current_span("compound.create_signal_record"):
                    signal_id = await database.create_signal(
                        signal_type=signal_type,
                        title=signal_title,
                        summary=signal_summary,
                        source_name=source_name,
                        score=score,
                        status="alerted",
                        metadata={
                            "score_breakdown": score_breakdown,
                            "matched_member_count": len(matched_members),
                            "matched_members": matched_members,
                            "new_plan_id": str(new_plan_id) if new_plan_id else None,
                            **signal_metadata,
                        },
                    )

                # ── Step 7: Create signal_alert for HITL approval ────────
                with self._tracer.start_as_current_span("compound.create_signal_alert"):
                    alert_id = await database.create_signal_alert(
                        family_id=family_id,
                        signal_id=str(signal_id) if signal_id else None,
                        signal_type=signal_type,
                        title=signal_title,
                        summary=signal_summary,
                        score=score,
                        matched_members=matched_members,
                        new_plan_id=str(new_plan_id) if new_plan_id else None,
                    )
                    span.set_attribute("alert.id", str(alert_id))

                logger.info(f"[compound] Signal alert created: {alert_id}")

                # ── Step 8: Write audit log ──────────────────────────────
                with self._tracer.start_as_current_span("compound.audit_log"):
                    await database.log_action(
                        action="signal_compound_action",
                        family_id=family_id,
                        entity_type="signal_alert",
                        entity_id=str(alert_id) if alert_id else None,
                        details={
                            "signal_title": signal_title,
                            "signal_type": signal_type,
                            "score": score,
                            "score_breakdown": score_breakdown,
                            "matched_member_count": len(matched_members),
                            "action_taken": action_taken,
                            "new_plan_id": str(new_plan_id) if new_plan_id else None,
                            "alert_id": str(alert_id) if alert_id else None,
                            "trace_id": trace_id,
                        },
                    )

                span.set_attribute("compound.action_taken", action_taken)
                span.set_attribute("compound.success", True)

                return CompoundResult(
                    family_id=family_id,
                    signal_title=signal_title,
                    signal_type=signal_type,
                    score=score,
                    recommendation="fire",
                    matched_members=matched_members,
                    action_taken=action_taken,
                    new_plan_id=str(new_plan_id) if new_plan_id else None,
                    alert_id=str(alert_id) if alert_id else None,
                    trace_id=trace_id,
                )

            except Exception as exc:
                span.set_attribute("compound.success", False)
                span.set_attribute("compound.error", str(exc))
                logger.error(f"[compound] Error handling fired signal: {exc}", exc_info=True)
                return CompoundResult(
                    family_id=family_id,
                    signal_title=signal_title,
                    signal_type=signal_type,
                    score=score,
                    recommendation="fire",
                    matched_members=matched_members,
                    action_taken="error",
                    error=str(exc),
                    trace_id=trace_id,
                )


# ---------------------------------------------------------------------------
# Helper: build signal context note for WellnessAgent
# ---------------------------------------------------------------------------

def _build_signal_note(
    *,
    signal_title: str,
    signal_summary: str,
    signal_type: str,
    score: int,
    score_breakdown: list[str],
    matched_members: list[dict],
) -> str:
    """
    Builds the special_notes string injected into WellnessAgent.generate_meal_plan().
    This is what causes the plan to change — the agent sees the new evidence
    and adjusts meals/supplements accordingly.
    """
    member_names = [m.get("name", "Unknown") for m in matched_members]
    match_reasons = []
    for m in matched_members:
        for reason in m.get("match_reasons", []):
            match_reasons.append(f"  • {m.get('name')}: {reason}")

    if signal_type == "research":
        note = (
            f"⚠️  SIGNAL-DRIVEN REGENERATION — New peer-reviewed research detected.\n\n"
            f"Signal: {signal_title}\n"
            f"Summary: {signal_summary}\n\n"
            f"Signal score: {score}/10 (threshold: 5) — FIRED\n"
            f"Score breakdown:\n"
            + "\n".join(f"  {b}" for b in score_breakdown)
            + f"\n\nAffected family members: {', '.join(member_names)}\n"
            f"Match reasons:\n" + "\n".join(match_reasons)
            + "\n\nINSTRUCTION: Please regenerate the meal plan taking this new research "
            f"into account for the affected members. If the research supports adding, "
            f"removing, or modifying foods or supplements, reflect that in the plan. "
            f"Note in each affected meal's why_it_works field how this new evidence "
            f"influenced the recommendation."
        )
    else:
        note = (
            f"⚠️  SIGNAL-DRIVEN REGENERATION — Market price signal detected.\n\n"
            f"Signal: {signal_title}\n"
            f"Summary: {signal_summary}\n\n"
            f"Signal score: {score}/10 (threshold: 5) — FIRED\n"
            f"Affected family members: {', '.join(member_names)}\n\n"
            f"INSTRUCTION: Please regenerate the meal plan with budget-conscious "
            f"substitutions for items flagged by the price signal. Prioritize "
            f"equivalent nutritional value at lower cost. Note substitutions in "
            f"each meal's why_it_works field."
        )
    return note


# ---------------------------------------------------------------------------
# Helper: hydrate Family model from raw Supabase dict
# ---------------------------------------------------------------------------

def _hydrate_family(data: dict) -> Family:
    """
    Convert raw Supabase row dict → Family Pydantic model.
    Mirrors the logic in database.py / routes/family.py.
    """
    raw_members = data.get("members", [])
    members = []
    for m in raw_members:
        try:
            members.append(FamilyMember(
                id=m.get("id"),
                family_id=m.get("family_id"),
                member_number=m.get("member_number"),
                name=m.get("name", ""),
                age=m.get("age", 0),
                life_stage=LifeStage(m.get("life_stage", "adult")),
                sex=Sex(m.get("sex", "prefer_not_to_say")),
                activity_level=ActivityLevel(m.get("activity_level", "moderately_active")),
                dietary_style=DietaryStyle(m.get("dietary_style", "omnivore")),
                wellness_philosophy=WellnessPhilosophy(
                    m.get("wellness_philosophy", "no_preference")
                ),
                dosha=DoshaType(m.get("dosha", "unknown")) if m.get("dosha") else DoshaType.unknown,
                goals=m.get("goals") or [],
                allergies=m.get("allergies") or [],
                dislikes=m.get("dislikes") or [],
                loves=m.get("loves") or [],
                cuisine_prefs=m.get("cuisine_prefs") or [],
                health_conditions=m.get("health_conditions") or [],
                current_supplements=m.get("current_supplements") or [],
                supplements_open=m.get("supplements_open", True),
            ))
        except Exception as e:
            logger.warning(f"[compound] Skipping member {m.get('name')}: {e}")

    return Family(
        id=data.get("id"),
        client_number=data.get("client_number", ""),
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone"),
        budget_weekly=float(data.get("budget_weekly", 200)),
        quality_preference=QualityPreference(
            data.get("quality_preference", "whole_foods")
        ),
        plan_frequency=PlanFrequency(data.get("plan_frequency", "weekly")),
        notify_email=data.get("notify_email", True),
        notify_inapp=data.get("notify_inapp", True),
        members=members,
    )
