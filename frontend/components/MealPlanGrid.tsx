"use client";

import { useState } from "react";
import {
  Clock,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  UtensilsCrossed,
  Sparkles,
  Info,
} from "lucide-react";

interface Ingredient {
  name: string;
  quantity: string;
  unit: string;
  notes?: string;
}

interface Meal {
  id: string;
  name: string;
  prep_time: number;
  cook_time: number;
  ingredients: Ingredient[];
  instructions: string[];
  why_it_works: Record<string, string>;
  member_compatibility: string[];
  tags: string[];
  cuisine_type?: string;
}

interface DayMeals {
  day: string;
  breakfast?: Meal;
  lunch?: Meal;
  dinner?: Meal;
  snacks: Meal[];
}

interface MealPlan {
  id: string;
  family_id: string;
  week_start: string;
  days: DayMeals[];
  notes?: string;
}

interface Props {
  mealPlan: MealPlan | null;
  isLoading: boolean;
  onGeneratePlan: () => void;
  weekStart: string;
  familyId: string;
}

// ─── Meal Card ────────────────────────────────────────────────────────────────

function MealCard({ meal, type }: { meal: Meal; type: string }) {
  const [expanded, setExpanded] = useState(false);
  const totalTime = meal.prep_time + meal.cook_time;

  const typeConfig: Record<string, { color: string; dot: string }> = {
    breakfast: { color: "text-warm-600", dot: "bg-warm-400" },
    lunch: { color: "text-blue-600", dot: "bg-blue-400" },
    dinner: { color: "text-brand-600", dot: "bg-brand-400" },
    snack: { color: "text-purple-600", dot: "bg-purple-400" },
  };
  const cfg = typeConfig[type] || typeConfig.lunch;

  return (
    <div className="group">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left"
      >
        <div className="flex items-start gap-1.5 mb-1">
          <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${cfg.dot}`} />
          <p className="text-xs font-medium text-stone-800 leading-tight group-hover:text-brand-700 transition-colors">
            {meal.name}
          </p>
        </div>
        <div className="flex items-center gap-2 pl-3">
          <span className="flex items-center gap-1 text-xs text-stone-400">
            <Clock className="w-3 h-3" />
            {totalTime}m
          </span>
          {meal.tags?.slice(0, 1).map((tag) => (
            <span
              key={tag}
              className="text-xs bg-stone-100 text-stone-400 px-1.5 py-0.5 rounded-full"
            >
              {tag}
            </span>
          ))}
          {expanded ? (
            <ChevronUp className="w-3 h-3 text-stone-300 ml-auto" />
          ) : (
            <ChevronDown className="w-3 h-3 text-stone-300 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="mt-2 pl-3 space-y-3 animate-slide-up">
          {/* Why it works */}
          {Object.keys(meal.why_it_works).length > 0 && (
            <div className="p-2.5 bg-brand-50 rounded-lg border border-brand-100">
              <div className="flex items-center gap-1 mb-1.5">
                <Info className="w-3 h-3 text-brand-500" />
                <span className="text-xs font-semibold text-brand-700">
                  Why it works
                </span>
              </div>
              {Object.entries(meal.why_it_works).map(([member, reason]) => (
                <p key={member} className="text-xs text-stone-600 leading-relaxed">
                  <span className="font-medium text-stone-800">{member}:</span>{" "}
                  {reason}
                </p>
              ))}
            </div>
          )}

          {/* Ingredients */}
          <div>
            <p className="text-xs font-semibold text-stone-500 mb-1.5">Ingredients</p>
            <ul className="space-y-0.5">
              {meal.ingredients.slice(0, 5).map((ing, i) => (
                <li key={i} className="text-xs text-stone-600">
                  · {ing.quantity} {ing.unit} {ing.name}
                  {ing.notes && (
                    <span className="text-stone-400"> ({ing.notes})</span>
                  )}
                </li>
              ))}
              {meal.ingredients.length > 5 && (
                <li className="text-xs text-stone-400">
                  + {meal.ingredients.length - 5} more ingredients
                </li>
              )}
            </ul>
          </div>

          {/* Instructions preview */}
          {meal.instructions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-stone-500 mb-1.5">Instructions</p>
              <ol className="space-y-1">
                {meal.instructions.slice(0, 3).map((step, i) => (
                  <li key={i} className="text-xs text-stone-600 flex gap-1.5">
                    <span className="font-medium text-stone-400 flex-shrink-0">
                      {i + 1}.
                    </span>
                    {step}
                  </li>
                ))}
                {meal.instructions.length > 3 && (
                  <li className="text-xs text-stone-400">
                    + {meal.instructions.length - 3} more steps
                  </li>
                )}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Day Column ────────────────────────────────────────────────────────────────

function DayColumn({ day }: { day: DayMeals }) {
  return (
    <div className="bg-white rounded-xl border border-stone-100 overflow-hidden h-full flex flex-col">
      {/* Day header */}
      <div className="px-3 py-2 bg-stone-50 border-b border-stone-100">
        <p className="text-xs font-bold text-stone-700 uppercase tracking-wide">
          {day.day.slice(0, 3)}
        </p>
      </div>

      <div className="p-3 space-y-4 flex-1">
        {/* Breakfast */}
        <div>
          <p className="text-xs font-semibold text-warm-600 uppercase tracking-wide mb-2">
            Breakfast
          </p>
          {day.breakfast ? (
            <MealCard meal={day.breakfast} type="breakfast" />
          ) : (
            <p className="text-xs text-stone-300 italic">—</p>
          )}
        </div>

        {/* Lunch */}
        <div>
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">
            Lunch
          </p>
          {day.lunch ? (
            <MealCard meal={day.lunch} type="lunch" />
          ) : (
            <p className="text-xs text-stone-300 italic">—</p>
          )}
        </div>

        {/* Dinner */}
        <div>
          <p className="text-xs font-semibold text-brand-600 uppercase tracking-wide mb-2">
            Dinner
          </p>
          {day.dinner ? (
            <MealCard meal={day.dinner} type="dinner" />
          ) : (
            <p className="text-xs text-stone-300 italic">—</p>
          )}
        </div>

        {/* Snacks */}
        {day.snacks?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-2">
              Snacks
            </p>
            {day.snacks.map((snack, i) => (
              <MealCard key={i} meal={snack} type="snack" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main MealPlanGrid ────────────────────────────────────────────────────────

export default function MealPlanGrid({
  mealPlan,
  isLoading,
  onGeneratePlan,
  weekStart,
}: Props) {
  if (isLoading) {
    return (
      <div className="card p-12 text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-brand-100 rounded-2xl flex items-center justify-center animate-pulse-gentle">
            <Sparkles className="w-8 h-8 text-brand-500" />
          </div>
          <div>
            <p className="font-semibold text-stone-700 mb-1">
              Crafting your meal plan...
            </p>
            <p className="text-sm text-stone-400">
              Claude is personalizing meals for every family member. This takes about 30 seconds.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!mealPlan) {
    return (
      <div className="card p-12 text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-stone-100 rounded-2xl flex items-center justify-center">
            <UtensilsCrossed className="w-8 h-8 text-stone-400" />
          </div>
          <div>
            <p className="font-semibold text-stone-700 mb-1">
              No meal plan yet
            </p>
            <p className="text-sm text-stone-400 mb-6">
              Click "Generate Plan" to create a personalized 7-day meal plan for your family.
            </p>
            <button onClick={onGeneratePlan} className="btn-primary">
              <Sparkles className="w-4 h-4 mr-2" />
              Generate My Meal Plan
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="section-title text-lg">Weekly Meal Plan</h2>
          {mealPlan.notes && (
            <p className="text-sm text-stone-500 mt-0.5">{mealPlan.notes}</p>
          )}
        </div>
        <button
          onClick={onGeneratePlan}
          className="flex items-center gap-1.5 text-sm text-stone-500 hover:text-brand-600 transition-colors font-medium"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Regenerate
        </button>
      </div>

      {/* 7-column grid */}
      <div className="grid grid-cols-7 gap-2" style={{ minHeight: "400px" }}>
        {mealPlan.days.map((day) => (
          <DayColumn key={day.day} day={day} />
        ))}
      </div>
    </div>
  );
}
