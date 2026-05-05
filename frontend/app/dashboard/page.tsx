"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Calendar,
  Sparkles,
  AlertCircle,
  Loader2,
} from "lucide-react";

function VitaRootsLogo({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 56 56" xmlns="http://www.w3.org/2000/svg">
      <path d="M28 40 Q20 44 13 49" stroke="#3B2010" strokeWidth="1.4" fill="none" strokeLinecap="round"/>
      <path d="M28 40 Q24 46 21 52" stroke="#3B2010" strokeWidth="1.1" fill="none" strokeLinecap="round"/>
      <path d="M28 40 Q29 47 28 53" stroke="#3B2010" strokeWidth="0.9" fill="none" strokeLinecap="round"/>
      <path d="M28 40 Q33 45 36 51" stroke="#3B2010" strokeWidth="1.1" fill="none" strokeLinecap="round"/>
      <path d="M28 40 Q35 43 42 48" stroke="#3B2010" strokeWidth="1.4" fill="none" strokeLinecap="round"/>
      <path d="M28 40 L28 18" stroke="#3E6B4A" strokeWidth="2.2" fill="none" strokeLinecap="round"/>
      <path d="M28 30 Q20 24 14 20" stroke="#3E6B4A" strokeWidth="1.6" fill="none" strokeLinecap="round"/>
      <path d="M28 24 Q22 17 17 13" stroke="#3E6B4A" strokeWidth="1.2" fill="none" strokeLinecap="round"/>
      <path d="M28 31 Q36 25 41 21" stroke="#3E6B4A" strokeWidth="1.6" fill="none" strokeLinecap="round"/>
      <path d="M28 24 Q34 17 39 13" stroke="#3E6B4A" strokeWidth="1.2" fill="none" strokeLinecap="round"/>
      <ellipse cx="13" cy="19" rx="5" ry="3" fill="#5E8A68" transform="rotate(-35 13 19)"/>
      <ellipse cx="42" cy="20" rx="5" ry="3" fill="#5E8A68" transform="rotate(35 42 20)"/>
      <ellipse cx="28" cy="13" rx="6" ry="3.5" fill="#2E4A35"/>
      <circle cx="11" cy="17" r="2" fill="#C05A2B"/>
      <circle cx="43" cy="18" r="2" fill="#C05A2B"/>
      <circle cx="28" cy="9" r="2.5" fill="#D6854A"/>
    </svg>
  );
}
import Link from "next/link";
import MealPlanGrid from "@/components/MealPlanGrid";
import GroceryList from "@/components/GroceryList";
import ChatAssistant from "@/components/ChatAssistant";
import FamilyMemberCard from "@/components/FamilyMemberCard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FamilyMember {
  id: string;
  name: string;
  age: number;
  life_stage: string;
  dietary_style: string;
  wellness_philosophy: string;
  goals: string[];
  dosha?: string;
}

interface Family {
  id: string;
  name: string;
  members: FamilyMember[];
  budget_weekly: number;
  quality_preference: string;
}

interface MealPlan {
  id: string;
  family_id: string;
  week_start: string;
  days: DayMeals[];
  notes?: string;
}

interface DayMeals {
  day: string;
  breakfast?: Meal;
  lunch?: Meal;
  dinner?: Meal;
  snacks: Meal[];
}

interface Meal {
  id: string;
  name: string;
  prep_time: number;
  cook_time: number;
  ingredients: { name: string; quantity: string; unit: string }[];
  instructions: string[];
  why_it_works: Record<string, string>;
  member_compatibility: string[];
  tags: string[];
}

interface GroceryListData {
  id: string;
  items: GroceryItem[];
  total_estimated_cost: number;
  budget_weekly: number;
}

interface GroceryItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: string;
  estimated_cost: number;
  quality_flag?: string;
  member_tags: string[];
  money_saving_tip?: string;
  checked: boolean;
}

function getWeekStart(offsetWeeks = 0): string {
  const d = new Date();
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Monday
  d.setDate(diff + offsetWeeks * 7);
  return d.toISOString().split("T")[0];
}

function formatWeekRange(startDate: string): string {
  const start = new Date(startDate);
  const end = new Date(startDate);
  end.setDate(end.getDate() + 6);
  return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${end.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const familyId = searchParams.get("family_id") || "";

  const [family, setFamily] = useState<Family | null>(null);
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(null);
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [groceryList, setGroceryList] = useState<GroceryListData | null>(null);
  const [weekOffset, setWeekOffset] = useState(0);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [isGeneratingGrocery, setIsGeneratingGrocery] = useState(false);
  const [error, setError] = useState("");
  const [loadingFamily, setLoadingFamily] = useState(true);

  const weekStart = getWeekStart(weekOffset);

  // Load family profile
  useEffect(() => {
    if (!familyId) {
      setLoadingFamily(false);
      return;
    }
    fetch(`${API_URL}/api/families/${familyId}`)
      .then((r) => r.json())
      .then((data) => {
        setFamily(data.data);
        if (data.data?.members?.[0]) {
          setSelectedMemberId(data.data.members[0].id);
        }
      })
      .catch(() => setError("Failed to load family profile."))
      .finally(() => setLoadingFamily(false));
  }, [familyId]);

  const handleGeneratePlan = async () => {
    if (!familyId) return;
    setIsGeneratingPlan(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/meal-plans/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ family_id: familyId, week_start: weekStart }),
      });
      if (!res.ok) throw new Error("Failed to generate meal plan.");
      const data = await res.json();
      setMealPlan(data.data);
      setGroceryList(null); // Reset grocery list when plan changes
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error generating plan.");
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const handleGenerateGrocery = async () => {
    if (!mealPlan || !family) return;
    setIsGeneratingGrocery(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/grocery-lists/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          family_id: familyId,
          meal_plan_id: mealPlan.id,
          budget: family.budget_weekly,
          quality_prefs: [family.quality_preference],
        }),
      });
      if (!res.ok) throw new Error("Failed to generate grocery list.");
      const data = await res.json();
      setGroceryList(data.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error generating grocery list.");
    } finally {
      setIsGeneratingGrocery(false);
    }
  };

  const handleToggleItem = async (itemId: string, checked: boolean) => {
    if (!groceryList) return;
    // Optimistic update
    setGroceryList((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.map((i) =>
              i.id === itemId ? { ...i, checked } : i
            ),
          }
        : prev
    );
    await fetch(`${API_URL}/api/grocery-items/${itemId}/check`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ checked }),
    }).catch(console.error);
  };

  if (loadingFamily) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  if (!familyId) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 text-center px-6">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ background: "rgba(62,107,74,0.1)" }}>
          <VitaRootsLogo size={36} />
        </div>
        <h2 className="text-2xl font-bold text-stone-900">No family profile found</h2>
        <p className="text-stone-500 max-w-sm">
          Start by creating your family's wellness profile to generate personalized plans.
        </p>
        <Link href="/onboarding" className="btn-primary">
          Create Family Profile
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col">
      {/* Top Navigation */}
      <header className="bg-white border-b border-stone-100 sticky top-0 z-40">
        <div className="max-w-screen-xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <VitaRootsLogo size={24} />
            <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "18px", fontWeight: 700, color: "#1E1208" }}>
              Vita<span style={{ color: "#3E6B4A" }}>Roots</span>
            </span>
          </div>

          {/* Week selector */}
          <div className="flex items-center gap-3 bg-stone-100 px-4 py-2 rounded-xl">
            <button
              onClick={() => setWeekOffset((w) => w - 1)}
              className="text-stone-600 hover:text-stone-900 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2 text-sm font-medium text-stone-700">
              <Calendar className="w-4 h-4 text-brand-500" />
              {formatWeekRange(weekStart)}
            </div>
            <button
              onClick={() => setWeekOffset((w) => w + 1)}
              className="text-stone-600 hover:text-stone-900 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={handleGeneratePlan}
            disabled={isGeneratingPlan}
            className="btn-primary py-2.5 text-sm"
          >
            {isGeneratingPlan ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Plan
              </>
            )}
          </button>
        </div>
      </header>

      {error && (
        <div className="max-w-screen-xl mx-auto w-full px-6 pt-4">
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        </div>
      )}

      <div className="flex-1 max-w-screen-xl mx-auto w-full px-6 py-6 flex gap-6">
        {/* Left sidebar — family members */}
        <aside className="w-56 flex-shrink-0 space-y-3">
          <h3 className="text-xs font-semibold text-stone-400 uppercase tracking-wider mb-3">
            Family Members
          </h3>
          {family?.members.map((member) => (
            <FamilyMemberCard
              key={member.id}
              member={member}
              isSelected={selectedMemberId === member.id}
              onSelect={() => setSelectedMemberId(member.id)}
            />
          ))}
          <Link
            href={`/onboarding`}
            className="flex items-center gap-2 text-sm text-brand-600 hover:text-brand-700 font-medium mt-4 transition-colors"
          >
            + Edit Family
          </Link>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 space-y-6">
          <MealPlanGrid
            mealPlan={mealPlan}
            isLoading={isGeneratingPlan}
            onGeneratePlan={handleGeneratePlan}
            weekStart={weekStart}
            familyId={familyId}
          />
        </main>

        {/* Right panel — grocery + budget */}
        <aside className="w-80 flex-shrink-0 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-stone-400 uppercase tracking-wider">
              Grocery List
            </h3>
            {mealPlan && !groceryList && (
              <button
                onClick={handleGenerateGrocery}
                disabled={isGeneratingGrocery}
                className="flex items-center gap-1.5 text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors"
              >
                {isGeneratingGrocery ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <RefreshCw className="w-3 h-3" />
                )}
                Generate
              </button>
            )}
          </div>
          <GroceryList
            groceryList={groceryList}
            isLoading={isGeneratingGrocery}
            budget={family?.budget_weekly || 0}
            onToggleItem={handleToggleItem}
          />
        </aside>
      </div>

      {/* Floating Chat Assistant */}
      <ChatAssistant
        familyId={familyId}
        family={family}
        selectedMemberId={selectedMemberId}
      />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
