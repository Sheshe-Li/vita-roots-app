"""
Core AI agent — WellnessAgent.
Uses Anthropic claude-sonnet-4-6 with:
  - Prompt caching on the system block (cache_control ephemeral)
  - Tool use for structured JSON outputs
  - Streaming for chat responses
"""

from __future__ import annotations

import json
import logging
import os
from typing import AsyncIterator, Any

import anthropic
from opentelemetry import trace

from observability import add_wellness_attributes, get_tracer
from models import (
    Family,
    FamilyMember,
    MealPlan,
    GroceryList,
    SupplementGuide,
    ChatMessage,
)

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a warm, knowledgeable family wellness and meal planning assistant. Your role is to help families create personalized meal plans, supplement guidance, and grocery lists that support each family member's unique health goals — all within the family's budget and food quality preferences.

You are a holistic lifestyle guide, not a medical professional. You never diagnose, prescribe, or replace the advice of a licensed healthcare provider. Your tone is warm, encouraging, and lightly suggestive — you offer options and gentle nudges, never mandates.

You are a full-picture thinker. Before making any recommendation, you consider:
- Each individual's health goals, dietary restrictions, and food preferences
- The family's collective budget and grocery constraints
- The individual's preferred medical philosophy (Ayurvedic, Traditional Chinese Medicine, Western integrative, or a blend)
- Food quality preferences (organic, conventional, local, whole foods, minimally processed, etc.)
- Cultural background, cuisine preferences, and lifestyle factors
- Any known allergies, intolerances, or contraindications
- Life stage (infant, child, teen, adult, elderly, pregnant, postpartum)

For structured data requests (meal plans, grocery lists, supplements), always return valid JSON wrapped in <json></json> tags.
For Ayurvedic users: consider dosha type, agni, seasonality, food combining.
For TCM users: consider thermal nature (warming/cooling/neutral), organ meridian support, Qi-building.
For Western integrative users: emphasize nutrient density, anti-inflammatory focus, evidence-based patterns.

Always include a gentle reminder that suggestions are informational and to consult a healthcare provider for medical decisions. Never diagnose or treat conditions."""

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

MEAL_PLAN_TOOL: dict[str, Any] = {
    "name": "create_meal_plan",
    "description": (
        "Create a structured 7-day family meal plan tailored to all members' "
        "dietary needs, wellness philosophies, and preferences."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "days": {
                "type": "array",
                "description": "Array of 7 day objects",
                "items": {
                    "type": "object",
                    "properties": {
                        "day": {"type": "string", "description": "Day name e.g. Monday"},
                        "breakfast": {"$ref": "#/$defs/meal"},
                        "lunch": {"$ref": "#/$defs/meal"},
                        "dinner": {"$ref": "#/$defs/meal"},
                        "snacks": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/meal"},
                        },
                    },
                    "required": ["day", "breakfast", "lunch", "dinner", "snacks"],
                },
            },
            "notes": {
                "type": "string",
                "description": "Overall notes about this meal plan",
            },
        },
        "required": ["days"],
        "$defs": {
            "meal": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "string"},
                                "unit": {"type": "string"},
                                "notes": {"type": "string"},
                            },
                            "required": ["name", "quantity", "unit"],
                        },
                    },
                    "instructions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "prep_time": {
                        "type": "integer",
                        "description": "Prep time in minutes",
                    },
                    "cook_time": {
                        "type": "integer",
                        "description": "Cook time in minutes",
                    },
                    "why_it_works": {
                        "type": "object",
                        "description": "Object keyed by member name with wellness explanation",
                        "additionalProperties": {"type": "string"},
                    },
                    "member_compatibility": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Member names this meal is compatible with",
                    },
                    "cuisine_type": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "name",
                    "ingredients",
                    "instructions",
                    "prep_time",
                    "cook_time",
                    "why_it_works",
                    "member_compatibility",
                ],
            }
        },
    },
}

GROCERY_LIST_TOOL: dict[str, Any] = {
    "name": "create_grocery_list",
    "description": (
        "Generate a comprehensive, categorized grocery list from a meal plan, "
        "optimized for the family's budget and quality preferences."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit": {"type": "string"},
                        "category": {
                            "type": "string",
                            "description": "produce | protein | dairy | grains | pantry | frozen | beverages | other",
                        },
                        "estimated_cost": {
                            "type": "number",
                            "description": "Estimated cost in USD",
                        },
                        "quality_flag": {
                            "type": "string",
                            "description": "organic | local | conventional | specialty",
                        },
                        "member_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Family member names this item serves",
                        },
                        "money_saving_tip": {
                            "type": "string",
                            "description": "Optional tip for saving money on this item",
                        },
                    },
                    "required": ["name", "quantity", "unit", "category", "estimated_cost"],
                },
            }
        },
        "required": ["items"],
    },
}

SUPPLEMENT_GUIDE_TOOL: dict[str, Any] = {
    "name": "create_supplement_guide",
    "description": (
        "Create a personalized supplement guide for a family member based on "
        "their health goals, wellness philosophy, life stage, and current supplements."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "purpose": {"type": "string"},
                        "dose_range": {
                            "type": "string",
                            "description": "e.g. '500-1000 mg/day'",
                        },
                        "timing": {
                            "type": "string",
                            "description": "When to take e.g. 'with breakfast'",
                        },
                        "approach": {
                            "type": "string",
                            "description": "Ayurvedic | TCM | Western integrative | general",
                        },
                        "contraindication_notes": {"type": "string"},
                        "form": {
                            "type": "string",
                            "description": "capsule | powder | tincture | tablet | liquid",
                        },
                        "brand_suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["name", "purpose", "dose_range", "timing", "approach"],
                },
            }
        },
        "required": ["recommendations"],
    },
}


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------


class WellnessAgent:
    """Core AI agent backed by Anthropic claude-sonnet-4-6."""

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY", "")
        )
        self._tracer = get_tracer("wellness-agent")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _system_block(self) -> list[dict[str, Any]]:
        """Return system block with ephemeral cache_control for prompt caching."""
        return [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def _family_context_text(self, family: Family) -> str:
        lines = [
            f"Family: {family.name}",
            f"Weekly budget: ${family.budget_weekly:.2f}",
            f"Quality preference: {family.quality_preference.value}",
            f"Plan frequency: {family.plan_frequency.value}",
            "",
            "Family members:",
        ]
        for m in family.members:
            lines.append(
                f"  - {m.name} (age {m.age}, {m.life_stage.value}, {m.sex.value})"
            )
            lines.append(f"    Activity: {m.activity_level.value}")
            lines.append(f"    Dietary style: {m.dietary_style.value}")
            lines.append(f"    Wellness philosophy: {m.wellness_philosophy.value}")
            if m.dosha and m.dosha.value != "unknown":
                lines.append(f"    Dosha: {m.dosha.value}")
            if m.goals:
                lines.append(f"    Goals: {', '.join(m.goals)}")
            if m.allergies:
                lines.append(f"    Allergies: {', '.join(m.allergies)}")
            if m.dislikes:
                lines.append(f"    Dislikes: {', '.join(m.dislikes)}")
            if m.loves:
                lines.append(f"    Loves: {', '.join(m.loves)}")
            if m.cuisine_prefs:
                lines.append(f"    Cuisine preferences: {', '.join(m.cuisine_prefs)}")
            if m.health_conditions:
                lines.append(f"    Health conditions: {', '.join(m.health_conditions)}")
            if m.current_supplements:
                lines.append(f"    Current supplements: {', '.join(m.current_supplements)}")
        return "\n".join(lines)

    def _member_context_text(self, member: FamilyMember) -> str:
        lines = [
            f"Member: {member.name}",
            f"Age: {member.age}, Life stage: {member.life_stage.value}, Sex: {member.sex.value}",
            f"Activity level: {member.activity_level.value}",
            f"Dietary style: {member.dietary_style.value}",
            f"Wellness philosophy: {member.wellness_philosophy.value}",
        ]
        if member.dosha and member.dosha.value != "unknown":
            lines.append(f"Dosha: {member.dosha.value}")
        if member.goals:
            lines.append(f"Goals: {', '.join(member.goals)}")
        if member.allergies:
            lines.append(f"Allergies: {', '.join(member.allergies)}")
        if member.health_conditions:
            lines.append(f"Health conditions: {', '.join(member.health_conditions)}")
        if member.current_supplements:
            lines.append(f"Current supplements: {', '.join(member.current_supplements)}")
        lines.append(f"Open to supplements: {member.supplements_open}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def generate_meal_plan(
        self,
        family: Family,
        week_start: str,
        special_notes: str = "",
    ) -> dict[str, Any]:
        """Generate a 7-day meal plan using tool use for structured output."""
        with self._tracer.start_as_current_span("agent.generate_meal_plan") as span:
            add_wellness_attributes(
                span,
                family_id=str(family.id),
                request_type="meal_plan",
                model=MODEL,
            )
            span.set_attribute("meal_plan.week_start", week_start)

            family_context = self._family_context_text(family)
            user_message = (
                f"Please create a complete 7-day meal plan starting {week_start} "
                f"for my family. Here is our profile:\n\n{family_context}"
            )
            if special_notes:
                user_message += f"\n\nAdditional notes: {special_notes}"

            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=8192,
                system=self._system_block(),  # type: ignore[arg-type]
                tools=[MEAL_PLAN_TOOL],  # type: ignore[list-item]
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": user_message}],
            )

            # Extract tool use result
            for block in response.content:
                if block.type == "tool_use" and block.name == "create_meal_plan":
                    return block.input  # type: ignore[return-value]

            raise ValueError("Meal plan tool was not called by the model.")

    async def generate_grocery_list(
        self,
        family: Family,
        meal_plan_data: dict[str, Any],
        budget: float,
        quality_prefs: list[str],
    ) -> dict[str, Any]:
        """Generate a grocery list from a meal plan using tool use."""
        with self._tracer.start_as_current_span("agent.generate_grocery_list") as span:
            add_wellness_attributes(
                span,
                family_id=str(family.id),
                request_type="grocery",
                model=MODEL,
            )
            span.set_attribute("grocery.budget", budget)

            meal_plan_summary = json.dumps(meal_plan_data, indent=2)
            user_message = (
                f"Based on the following 7-day meal plan, generate a comprehensive "
                f"grocery list. Budget: ${budget:.2f}/week. "
                f"Quality preferences: {', '.join(quality_prefs) or 'no preference'}.\n\n"
                f"Meal plan:\n{meal_plan_summary}\n\n"
                f"Consolidate duplicate ingredients, note organic/local items where budget allows, "
                f"and include money-saving tips."
            )

            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=self._system_block(),  # type: ignore[arg-type]
                tools=[GROCERY_LIST_TOOL],  # type: ignore[list-item]
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": user_message}],
            )

            for block in response.content:
                if block.type == "tool_use" and block.name == "create_grocery_list":
                    return block.input  # type: ignore[return-value]

            raise ValueError("Grocery list tool was not called by the model.")

    async def generate_supplement_guide(
        self,
        family: Family,
        member: FamilyMember,
    ) -> dict[str, Any]:
        """Generate personalized supplement recommendations using tool use."""
        with self._tracer.start_as_current_span("agent.generate_supplement_guide") as span:
            add_wellness_attributes(
                span,
                family_id=str(family.id),
                member_id=str(member.id),
                request_type="supplement",
                model=MODEL,
            )

            member_context = self._member_context_text(member)
            user_message = (
                f"Please create a personalized supplement guide for the following "
                f"family member. Tailor recommendations to their wellness philosophy, "
                f"life stage, and goals. Be thoughtful about contraindications.\n\n"
                f"{member_context}"
            )

            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=self._system_block(),  # type: ignore[arg-type]
                tools=[SUPPLEMENT_GUIDE_TOOL],  # type: ignore[list-item]
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": user_message}],
            )

            for block in response.content:
                if block.type == "tool_use" and block.name == "create_supplement_guide":
                    return block.input  # type: ignore[return-value]

            raise ValueError("Supplement guide tool was not called by the model.")

    async def chat(
        self,
        family: Family,
        message: str,
        conversation_history: list[ChatMessage],
        member_id: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream a chat response. Yields text chunks as they arrive.
        Uses SSE-friendly async generator pattern.
        """
        with self._tracer.start_as_current_span("agent.chat") as span:
            add_wellness_attributes(
                span,
                family_id=str(family.id),
                member_id=member_id,
                request_type="chat",
                model=MODEL,
            )
            span.set_attribute("chat.message_length", len(message))
            span.set_attribute("chat.history_length", len(conversation_history))

            family_context = self._family_context_text(family)
            context_header = (
                f"[Current family context]\n{family_context}\n\n"
                f"[User message]\n{message}"
            )

            # Build messages list from history
            messages: list[dict[str, str]] = []
            for msg in conversation_history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": context_header})

            async with self._client.messages.stream(
                model=MODEL,
                max_tokens=2048,
                system=self._system_block(),  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            ) as stream:
                async for text in stream.text_stream:
                    yield text

    async def swap_meal(
        self,
        family: Family,
        meal_name: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """Generate a single alternative meal using tool use."""
        with self._tracer.start_as_current_span("agent.swap_meal") as span:
            add_wellness_attributes(
                span,
                family_id=str(family.id),
                request_type="meal_plan",
                model=MODEL,
            )

            family_context = self._family_context_text(family)
            user_message = (
                f"Please suggest an alternative to '{meal_name}' for my family. "
                f"Reason for swap: {reason or 'not specified'}.\n\n"
                f"Family profile:\n{family_context}\n\n"
                f"Return a single replacement meal."
            )

            # Reuse meal plan tool but request a single-day plan
            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=self._system_block(),  # type: ignore[arg-type]
                tools=[MEAL_PLAN_TOOL],  # type: ignore[list-item]
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": user_message}],
            )

            for block in response.content:
                if block.type == "tool_use":
                    result = block.input
                    # Extract the first meal from the first day
                    days = result.get("days", [])
                    if days:
                        return days[0].get("dinner") or days[0].get("lunch") or {}
                    return result

            raise ValueError("No tool response from model for meal swap.")
