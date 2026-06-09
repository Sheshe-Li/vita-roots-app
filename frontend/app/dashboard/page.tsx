"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronLeft, ChevronRight, RefreshCw, Calendar,
  Sparkles, AlertCircle, Loader2, LogOut, Menu, X,
} from "lucide-react";
import Link from "next/link";
import { createClient } from "@/lib/supabase";
import MealPlanGrid from "@/components/MealPlanGrid";
import GroceryList from "@/components/GroceryList";
import ChatAssistant from "@/components/ChatAssistant";
import FamilyMemberCard from "@/components/FamilyMemberCard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  client_number?: string;
}

interface MealPlan {
  id: string;
  family_id: string;
  week_start: string;
  days: DayMeals[];
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
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff + offsetWeeks * 7);
  return d.toISOString().split("T")[0];
}

function formatWeekRange(startDate: string): string {
  const start = new Date(startDate);
  const end = new Date(startDate);
  end.setDate(end.getDate() + 6);
  return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${end.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
}

export default function DashboardPage() {
  const router = useRouter();
  const supabase = createClient();

  const [family, setFamily] = useState<Family | null>(null);
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(null);
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [groceryList, setGroceryList] = useState<GroceryListData | null>(null);
  const [weekOffset, setWeekOffset] = useState(0);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [isGeneratingGrocery, setIsGeneratingGrocery] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const weekStart = getWeekStart(weekOffset);

  // Load family from auth session
  useEffect(() => {
    async function load() {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push("/login");
        return;
      }

      try {
        const res = await fetch(`${API_URL}/api/families/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!res.ok) throw new Error("Could not load family");
        const data = await res.json();
        setFamily(data.data);
        if (data.data?.members?.[0]) {
          setSelectedMemberId(data.data.members[0].id);
        }
      } catch {
        setError("Could not load your family profile. Please contact support.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  const handleGeneratePlan = async () => {
    if (!family) return;
    setIsGeneratingPlan(true);
    setError("");
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const res = await fetch(`${API_URL}/api/meal-plans/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(session ? { Authorization: `Bearer ${session.access_token}` } : {}),
        },
        body: JSON.stringify({ family_id: family.id, week_start: weekStart }),
      });
      if (!res.ok) throw new Error("Failed to generate meal plan.");
      const data = await res.json();
      setMealPlan(data.data);
      setGroceryList(null);
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
          family_id: family.id,
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
    setGroceryList((prev) =>
      prev ? { ...prev, items: prev.items.map((i) => i.id === itemId ? { ...i, checked } : i) } : prev
    );
    await fetch(`${API_URL}/api/grocery-items/${itemId}/check`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ checked }),
    }).catch(console.error);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-stone-50">
        <Loader2 className="w-8 h-8 text-green-700 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-stone-100 sticky top-0 z-40">
        <div className="px-4 sm:px-6 py-3 flex items-center gap-3">
          {/* Mobile menu toggle */}
          <button
            className="sm:hidden p-1.5 rounded-lg text-stone-600 hover:bg-stone-100"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          {/* Logo */}
          <div className="flex items-center gap-2 flex-1">
            <VitaRootsLogo size={22} />
            <span
              className="text-base font-bold hidden xs:block"
              style={{ fontFamily: "'Cormorant Garamond', serif", color: "#1E1208" }}
            >
              Vita<span style={{ color: "#3E6B4A" }}>Roots</span>
            </span>
            {family?.client_number && (
              <span className="ml-2 text-xs text-stone-400 hidden sm:block">{family.client_number}</span>
            )}
          </div>

          {/* Week selector — hidden on mobile, shown inline on sm+ */}
          <div className="hidden sm:flex items-center gap-2 bg-stone-100 px-3 py-1.5 rounded-xl text-sm font-medium text-stone-700">
            <button onClick={() => setWeekOffset((w) => w - 1)} className="text-stone-500 hover:text-stone-900">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <Calendar className="w-3.5 h-3.5 text-green-700" />
            <span className="text-xs">{formatWeekRange(weekStart)}</span>
            <button onClick={() => setWeekOffset((w) => w + 1)} className="text-stone-500 hover:text-stone-900">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Generate + sign out */}
          <button
            onClick={handleGeneratePlan}
            disabled={isGeneratingPlan}
            className="flex items-center gap-1.5 bg-green-700 hover:bg-green-800 disabled:opacity-60 text-white text-xs font-semibold px-3 py-2 rounded-xl transition"
          >
            {isGeneratingPlan ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Generate Plan</span>
            <span className="sm:hidden">Plan</span>
          </button>

          <button
            onClick={handleSignOut}
            className="p-2 rounded-xl text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>

        {/* Mobile week bar */}
        <div className="sm:hidden flex items-center justify-center gap-3 px-4 pb-2.5 text-sm text-stone-600">
          <button onClick={() => setWeekOffset((w) => w - 1)}><ChevronLeft className="w-4 h-4" /></button>
          <span className="text-xs font-medium">{formatWeekRange(weekStart)}</span>
          <button onClick={() => setWeekOffset((w) => w + 1)}><ChevronRight className="w-4 h-4" /></button>
        </div>
      </header>

      {error && (
        <div className="mx-4 sm:mx-6 mt-4">
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        </div>
      )}

      {/* Body layout: sidebar + main + grocery */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar — slide-over on mobile, static on sm+ */}
        <aside
          className={`
            fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-stone-100 pt-20 px-4 pb-6 overflow-y-auto
            transform transition-transform duration-200
            sm:static sm:transform-none sm:w-56 sm:pt-6 sm:z-auto sm:block
            ${sidebarOpen ? "translate-x-0 shadow-xl" : "-translate-x-full sm:translate-x-0"}
          `}
        >
          {/* Overlay close on mobile */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-20 bg-black/20 sm:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          <h3 className="text-xs font-semibold text-stone-400 uppercase tracking-wider mb-3 relative z-10">
            Family Members
          </h3>
          <div className="space-y-2 relative z-10">
            {family?.members.map((member) => (
              <div key={member.id} onClick={() => { setSelectedMemberId(member.id); setSidebarOpen(false); }}>
                <FamilyMemberCard
                  member={member}
                  isSelected={selectedMemberId === member.id}
                  onSelect={() => { setSelectedMemberId(member.id); setSidebarOpen(false); }}
                />
              </div>
            ))}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 px-4 sm:px-6 py-5 overflow-y-auto">
          <MealPlanGrid
            mealPlan={mealPlan}
            isLoading={isGeneratingPlan}
            onGeneratePlan={handleGeneratePlan}
            weekStart={weekStart}
            familyId={family?.id || ""}
          />
        </main>

        {/* Grocery panel — hidden on mobile (accessible via chat), shown on lg+ */}
        <aside className="hidden lg:block w-80 flex-shrink-0 px-4 py-5 overflow-y-auto border-l border-stone-100">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-stone-400 uppercase tracking-wider">
              Grocery List
            </h3>
            {mealPlan && !groceryList && (
              <button
                onClick={handleGenerateGrocery}
                disabled={isGeneratingGrocery}
                className="flex items-center gap-1.5 text-xs font-medium text-green-700 hover:text-green-800 transition"
              >
                {isGeneratingGrocery ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
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

      {/* Floating Chat */}
      <ChatAssistant
        familyId={family?.id || ""}
        family={family}
        selectedMemberId={selectedMemberId}
      />
    </div>
  );
}
