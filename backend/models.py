"""
Pydantic models for the Family Wellness App.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class LifeStage(str, Enum):
    INFANT = "infant"
    CHILD = "child"
    TEEN = "teen"
    ADULT = "adult"
    ELDERLY = "elderly"
    PREGNANT = "pregnant"
    POSTPARTUM = "postpartum"


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class DietaryStyle(str, Enum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    FLEXITARIAN = "flexitarian"
    KETO = "keto"
    PALEO = "paleo"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    HALAL = "halal"
    KOSHER = "kosher"
    RAW = "raw"
    WHOLE_FOOD_PLANT_BASED = "whole_food_plant_based"


class WellnessPhilosophy(str, Enum):
    AYURVEDIC = "ayurvedic"
    TCM = "tcm"
    WESTERN_INTEGRATIVE = "western_integrative"
    BLEND = "blend"
    NO_PREFERENCE = "no_preference"


class QualityPreference(str, Enum):
    ORGANIC = "organic"
    CONVENTIONAL = "conventional"
    LOCAL = "local"
    WHOLE_FOODS = "whole_foods"
    MINIMALLY_PROCESSED = "minimally_processed"
    BUDGET_FRIENDLY = "budget_friendly"


class PlanFrequency(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class DoshaType(str, Enum):
    VATA = "vata"
    PITTA = "pitta"
    KAPHA = "kapha"
    VATA_PITTA = "vata_pitta"
    PITTA_KAPHA = "pitta_kapha"
    VATA_KAPHA = "vata_kapha"
    TRIDOSHIC = "tridoshic"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Family & Member
# ---------------------------------------------------------------------------


class FamilyMember(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    age: int = Field(ge=0, le=120)
    life_stage: LifeStage
    sex: Sex = Sex.PREFER_NOT_TO_SAY
    activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE
    dietary_style: DietaryStyle = DietaryStyle.OMNIVORE
    wellness_philosophy: WellnessPhilosophy = WellnessPhilosophy.NO_PREFERENCE
    dosha: Optional[DoshaType] = DoshaType.UNKNOWN
    goals: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    loves: list[str] = Field(default_factory=list)
    cuisine_prefs: list[str] = Field(default_factory=list)
    supplements_open: bool = True
    current_supplements: list[str] = Field(default_factory=list)
    health_conditions: list[str] = Field(default_factory=list)


class FamilyMemberCreate(BaseModel):
    name: str
    age: int = Field(ge=0, le=120)
    life_stage: LifeStage
    sex: Sex = Sex.PREFER_NOT_TO_SAY
    activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE
    dietary_style: DietaryStyle = DietaryStyle.OMNIVORE
    wellness_philosophy: WellnessPhilosophy = WellnessPhilosophy.NO_PREFERENCE
    dosha: Optional[DoshaType] = DoshaType.UNKNOWN
    goals: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    loves: list[str] = Field(default_factory=list)
    cuisine_prefs: list[str] = Field(default_factory=list)
    supplements_open: bool = True
    current_supplements: list[str] = Field(default_factory=list)
    health_conditions: list[str] = Field(default_factory=list)


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=120)
    life_stage: Optional[LifeStage] = None
    sex: Optional[Sex] = None
    activity_level: Optional[ActivityLevel] = None
    dietary_style: Optional[DietaryStyle] = None
    wellness_philosophy: Optional[WellnessPhilosophy] = None
    dosha: Optional[DoshaType] = None
    goals: Optional[list[str]] = None
    allergies: Optional[list[str]] = None
    dislikes: Optional[list[str]] = None
    loves: Optional[list[str]] = None
    cuisine_prefs: Optional[list[str]] = None
    supplements_open: Optional[bool] = None
    current_supplements: Optional[list[str]] = None
    health_conditions: Optional[list[str]] = None


class Family(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    members: list[FamilyMember] = Field(default_factory=list)
    budget_weekly: float = Field(gt=0)
    quality_preference: QualityPreference = QualityPreference.WHOLE_FOODS
    plan_frequency: PlanFrequency = PlanFrequency.WEEKLY


class FamilyCreate(BaseModel):
    name: str
    members: list[FamilyMemberCreate] = Field(default_factory=list)
    budget_weekly: float = Field(gt=0)
    quality_preference: QualityPreference = QualityPreference.WHOLE_FOODS
    plan_frequency: PlanFrequency = PlanFrequency.WEEKLY


class FamilyUpdate(BaseModel):
    name: Optional[str] = None
    budget_weekly: Optional[float] = Field(default=None, gt=0)
    quality_preference: Optional[QualityPreference] = None
    plan_frequency: Optional[PlanFrequency] = None


# ---------------------------------------------------------------------------
# Meal Planning
# ---------------------------------------------------------------------------


class Ingredient(BaseModel):
    name: str
    quantity: str
    unit: str
    notes: Optional[str] = None


class Meal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    ingredients: list[Ingredient] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    prep_time: int = Field(description="Preparation time in minutes")
    cook_time: int = Field(description="Cooking time in minutes")
    why_it_works: dict[str, str] = Field(
        default_factory=dict,
        description="Keyed by member name, explains nutritional/wellness fit",
    )
    member_compatibility: list[str] = Field(
        default_factory=list,
        description="List of member names this meal suits",
    )
    cuisine_type: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class DayMeals(BaseModel):
    day: str
    breakfast: Optional[Meal] = None
    lunch: Optional[Meal] = None
    dinner: Optional[Meal] = None
    snacks: list[Meal] = Field(default_factory=list)


class MealPlan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    family_id: UUID
    week_start: str = Field(description="ISO date string YYYY-MM-DD")
    days: list[DayMeals] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: Optional[str] = None


class MealPlanRequest(BaseModel):
    family_id: str
    week_start: str = Field(description="ISO date string YYYY-MM-DD")
    special_notes: Optional[str] = None


class MealSwapRequest(BaseModel):
    meal_id: str
    reason: Optional[str] = None
    family_id: str


# ---------------------------------------------------------------------------
# Grocery List
# ---------------------------------------------------------------------------


class GroceryItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    quantity: float
    unit: str
    category: str = Field(description="e.g. produce, dairy, protein, pantry, frozen")
    estimated_cost: float = Field(ge=0)
    quality_flag: Optional[str] = Field(
        default=None,
        description="organic | local | conventional | etc.",
    )
    member_tags: list[str] = Field(
        default_factory=list,
        description="Which family members this item serves",
    )
    money_saving_tip: Optional[str] = None
    checked: bool = False


class GroceryList(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    family_id: UUID
    meal_plan_id: UUID
    items: list[GroceryItem] = Field(default_factory=list)
    total_estimated_cost: float = 0.0
    budget_weekly: float = 0.0
    created_at: Optional[str] = None

    def compute_total(self) -> float:
        self.total_estimated_cost = sum(i.estimated_cost for i in self.items)
        return self.total_estimated_cost


class GroceryListRequest(BaseModel):
    family_id: str
    meal_plan_id: str
    budget: float = Field(gt=0)
    quality_prefs: list[str] = Field(default_factory=list)


class GroceryItemCheckRequest(BaseModel):
    checked: bool


# ---------------------------------------------------------------------------
# Supplements
# ---------------------------------------------------------------------------


class SupplementRecommendation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    purpose: str
    dose_range: str = Field(description="e.g. '500–1000 mg/day'")
    timing: str = Field(description="e.g. 'with breakfast', 'before bed'")
    approach: str = Field(
        description="Ayurvedic | TCM | Western integrative | general",
    )
    contraindication_notes: Optional[str] = None
    form: Optional[str] = Field(default=None, description="capsule, powder, tincture…")
    brand_suggestions: list[str] = Field(default_factory=list)


class SupplementGuide(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    family_id: UUID
    member_id: UUID
    member_name: str
    recommendations: list[SupplementRecommendation] = Field(default_factory=list)
    disclaimer: str = (
        "These suggestions are informational only. "
        "Please consult a licensed healthcare provider before starting any supplement."
    )
    created_at: Optional[str] = None


class SupplementRequest(BaseModel):
    family_id: str


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str = Field(description="user | assistant")
    content: str


class ChatRequest(BaseModel):
    family_id: str
    message: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    member_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    family_id: str
    member_id: Optional[str] = None


# ---------------------------------------------------------------------------
# API response wrappers
# ---------------------------------------------------------------------------


class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: Optional[str] = None


class HealthCheck(BaseModel):
    status: str
    phoenix_connected: bool
    phoenix_endpoint: str
    version: str = "1.0.0"
