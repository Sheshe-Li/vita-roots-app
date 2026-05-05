"use client";

import { useState } from "react";
import {
  ShoppingCart, Heart, Sparkles, ChevronDown, ChevronUp,
  Check, Star, Shield, Users, AlertCircle, X, MessageCircle,
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
import {
  DEMO_FAMILY, DEMO_MEAL_PLAN, DEMO_GROCERY_LIST, DEMO_SUPPLEMENTS,
} from "@/lib/demo-data";

// ─── helpers ────────────────────────────────────────────────────────────────

const PHILOSOPHY_COLORS: Record<string, string> = {
  ayurvedic: "bg-amber-100 text-amber-700",
  western_integrative: "bg-blue-100 text-blue-700",
  tcm: "bg-green-100 text-green-700",
  blend: "bg-purple-100 text-purple-700",
};

const CATEGORY_ORDER = ["produce", "protein", "dairy", "grains", "pantry", "frozen", "other"];

const CATEGORY_LABELS: Record<string, string> = {
  produce: "🥦 Produce",
  protein: "🥩 Protein",
  dairy: "🥛 Dairy & Alternatives",
  grains: "🌾 Grains & Bread",
  pantry: "🫙 Pantry",
  frozen: "🧊 Frozen",
  other: "📦 Other",
};

type SupplementKey = keyof typeof DEMO_SUPPLEMENTS;

// ─── sub-components ─────────────────────────────────────────────────────────

function PhilosophyBadge({ philosophy, dosha }: { philosophy: string; dosha?: string | null }) {
  const label = philosophy === "ayurvedic"
    ? `Ayurvedic${dosha ? ` · ${dosha.charAt(0).toUpperCase() + dosha.slice(1)}` : ""}`
    : philosophy === "western_integrative" ? "Western Integrative"
    : philosophy === "tcm" ? "TCM"
    : "Blend";
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${PHILOSOPHY_COLORS[philosophy] ?? "bg-stone-100 text-stone-600"}`}>
      {label}
    </span>
  );
}

function MemberTab({
  member, selected, onClick,
}: { member: (typeof DEMO_FAMILY.members)[0]; selected: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-1 px-4 py-3 rounded-xl transition-all border ${
        selected
          ? "bg-brand-600 text-white border-brand-600 shadow"
          : "bg-white text-stone-600 border-stone-200 hover:border-brand-300"
      }`}
    >
      <div className={`w-9 h-9 rounded-full flex items-center justify-center text-base font-bold ${
        selected ? "bg-white/20 text-white" : "bg-brand-100 text-brand-700"
      }`}>
        {member.name[0]}
      </div>
      <span className="text-xs font-semibold">{member.name}</span>
      <span className={`text-xs ${selected ? "text-brand-100" : "text-stone-400"}`}>
        {member.age} · {member.life_stage}
      </span>
    </button>
  );
}

function MealCard({ meal, members }: { meal: any; members: (typeof DEMO_FAMILY.members) }) {
  const [open, setOpen] = useState(false);
  if (!meal) return null;
  return (
    <div className="bg-white border border-stone-100 rounded-xl overflow-hidden hover:shadow-sm transition-shadow">
      <button onClick={() => setOpen(!open)} className="w-full text-left p-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs font-semibold text-stone-500 uppercase tracking-wide mb-0.5">
              {meal.cuisine_type}
            </p>
            <p className="text-sm font-bold text-stone-900 leading-snug">{meal.name}</p>
            <p className="text-xs text-stone-400 mt-1">
              ⏱ {meal.prep_time + meal.cook_time} min &nbsp;·&nbsp;
              {meal.tags?.slice(0, 2).join(" · ")}
            </p>
          </div>
          {open ? <ChevronUp className="w-4 h-4 text-stone-400 flex-shrink-0 mt-1" /> : <ChevronDown className="w-4 h-4 text-stone-400 flex-shrink-0 mt-1" />}
        </div>
        {/* compatibility dots */}
        <div className="flex gap-1 mt-2">
          {members.map((m) => (
            <span
              key={m.id}
              title={m.name}
              className={`w-5 h-5 rounded-full text-xs flex items-center justify-center font-bold ${
                meal.member_compatibility?.includes(m.name)
                  ? "bg-brand-100 text-brand-700"
                  : "bg-stone-100 text-stone-300"
              }`}
            >
              {m.name[0]}
            </span>
          ))}
        </div>
      </button>
      {open && (
        <div className="border-t border-stone-100 p-3 space-y-3 bg-stone-50/60">
          <div>
            <p className="text-xs font-semibold text-stone-500 mb-1">Ingredients</p>
            <ul className="text-xs text-stone-600 space-y-0.5">
              {meal.ingredients?.map((ing: any, i: number) => (
                <li key={i}>• {ing.quantity} {ing.unit} {ing.name}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-stone-500 mb-1">Why it works</p>
            {Object.entries(meal.why_it_works ?? {}).map(([name, reason]) => (
              <p key={name} className="text-xs text-stone-600">
                <span className="font-semibold text-brand-700">{name}:</span> {reason as string}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function GrocerySection() {
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const total = DEMO_GROCERY_LIST.total_estimated_cost;
  const budget = DEMO_GROCERY_LIST.budget_weekly;
  const spent = DEMO_GROCERY_LIST.items
    .filter((i) => checked.has(i.id))
    .reduce((s, i) => s + i.estimated_cost, 0);
  const pct = Math.min((total / budget) * 100, 100);

  const byCategory = CATEGORY_ORDER.reduce<Record<string, typeof DEMO_GROCERY_LIST.items>>(
    (acc, cat) => {
      const items = DEMO_GROCERY_LIST.items.filter((i) => i.category === cat);
      if (items.length) acc[cat] = items;
      return acc;
    }, {}
  );

  return (
    <div className="space-y-4">
      {/* budget bar */}
      <div className="bg-white border border-stone-200 rounded-xl p-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="font-semibold text-stone-700">Weekly Budget</span>
          <span className={total > budget ? "text-red-600 font-bold" : "text-brand-600 font-bold"}>
            ${total.toFixed(2)} / ${budget}
          </span>
        </div>
        <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${total > budget ? "bg-red-500" : "bg-brand-500"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-stone-400 mt-1">
          ${(budget - total).toFixed(2)} under budget · {DEMO_GROCERY_LIST.items.length} items
        </p>
      </div>

      {/* categories */}
      {Object.entries(byCategory).map(([cat, items]) => (
        <div key={cat}>
          <p className="text-xs font-bold text-stone-500 uppercase tracking-wider mb-2">
            {CATEGORY_LABELS[cat] ?? cat}
          </p>
          <div className="space-y-1.5">
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => setChecked((prev) => {
                  const next = new Set(prev);
                  next.has(item.id) ? next.delete(item.id) : next.add(item.id);
                  return next;
                })}
                className={`w-full flex items-start gap-2 p-2.5 rounded-lg border text-left transition-all ${
                  checked.has(item.id)
                    ? "bg-stone-50 border-stone-100 opacity-50"
                    : "bg-white border-stone-100 hover:border-brand-200"
                }`}
              >
                <div className={`w-4 h-4 rounded flex-shrink-0 mt-0.5 border flex items-center justify-center transition-colors ${
                  checked.has(item.id) ? "bg-brand-500 border-brand-500" : "border-stone-300"
                }`}>
                  {checked.has(item.id) && <Check className="w-2.5 h-2.5 text-white" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-sm font-medium text-stone-800">{item.name}</span>
                    {item.quality_flag === "organic" && (
                      <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">organic</span>
                    )}
                    {item.quality_flag === "specialty" && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded-full font-medium">★ priority</span>
                    )}
                  </div>
                  <p className="text-xs text-stone-400">
                    {item.quantity} {item.unit} · ~${item.estimated_cost.toFixed(2)}
                  </p>
                  {item.money_saving_tip && (
                    <p className="text-xs text-amber-600 mt-0.5">💡 {item.money_saving_tip}</p>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function SupplementSection({ memberId }: { memberId: string }) {
  const data = DEMO_SUPPLEMENTS[memberId as SupplementKey];
  if (!data) return <p className="text-sm text-stone-400">No supplement data for this member.</p>;

  return (
    <div className="space-y-3">
      {data.recommendations.map((rec, i) => (
        <div key={i} className="bg-white border border-stone-100 rounded-xl p-4 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <p className="font-semibold text-stone-900 text-sm">{rec.name}</p>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${
              rec.approach === "Ayurvedic" ? "bg-amber-100 text-amber-700"
              : rec.approach === "Western integrative" ? "bg-blue-100 text-blue-700"
              : rec.approach.includes("TCM") ? "bg-green-100 text-green-700"
              : "bg-stone-100 text-stone-600"
            }`}>{rec.approach}</span>
          </div>
          <p className="text-xs text-stone-600">{rec.purpose}</p>
          <div className="flex flex-wrap gap-3 text-xs text-stone-500">
            <span>💊 {rec.form}</span>
            <span>📏 {rec.dose_range}</span>
            <span>⏰ {rec.timing}</span>
          </div>
          {rec.contraindication_notes && (
            <p className={`text-xs flex gap-1.5 ${rec.contraindication_notes.includes("⚠") ? "text-red-600" : "text-stone-400"}`}>
              <AlertCircle className="w-3 h-3 flex-shrink-0 mt-0.5" />
              {rec.contraindication_notes}
            </p>
          )}
        </div>
      ))}
      <p className="text-xs text-stone-400 italic pt-1">
        Supplement suggestions are informational only. Always consult a healthcare provider before starting any new supplement.
      </p>
    </div>
  );
}

// ─── Demo Chat ───────────────────────────────────────────────────────────────

function DemoChat({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hi! I'm your Family Wellness assistant 🌿 I know the Rivera family's profiles. How can I help you today?\n\nTry asking me:\n• \"Why is kitchari good for the whole family?\"\n• \"Suggest a snack for Mateo that's peanut-free\"\n• \"What supplements should Sofia prioritize first?\"",
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);

  const send = async () => {
    const msg = input.trim();
    if (!msg || streaming) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setStreaming(true);

    // Build a family context string for the system
    const familyCtx = `Family: The Rivera Family. Budget: $275/week. Members: Maria (42, Ayurvedic Pitta, perimenopausal, gluten-free), David (45, Western integrative, elevated cholesterol, no shellfish), Sofia (16, Vegetarian, Ayurvedic Vata, dairy-free, needs iron & B12), Mateo (9, omnivore, peanut-free, active child).`;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          family_id: "demo-family-001",
          family_context: familyCtx,
          message: msg,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      if (!res.body) throw new Error("No stream");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split("\n")) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data === "[DONE]") break;
            try {
              const parsed = JSON.parse(data);
              buffer += parsed.text ?? "";
              setMessages((prev) => [
                ...prev.slice(0, -1),
                { role: "assistant", content: buffer },
              ]);
            } catch { /* skip non-JSON lines */ }
          }
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "I'm having trouble connecting right now. Make sure ANTHROPIC_API_KEY is set and the backend is running." },
      ]);
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 w-96 max-h-[560px] rounded-2xl shadow-2xl flex flex-col z-50" style={{ background: "#FDFAF4", border: "1px solid rgba(201,169,110,0.25)" }}>
      <div className="flex items-center justify-between px-4 py-3 rounded-t-2xl" style={{ background: "#1E1208", borderBottom: "1px solid rgba(201,169,110,0.18)" }}>
        <div className="flex items-center gap-2" style={{ color: "#FAF5ED" }}>
          <VitaRootsLogo size={16} />
          <span className="font-semibold text-sm" style={{ fontFamily: "'Jost', sans-serif" }}>VitaRoots Assistant</span>
          <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: "rgba(214,133,74,0.2)", color: "#D6854A", fontSize: "9px", letterSpacing: "0.1em" }}>LIVE AI</span>
        </div>
        <button onClick={onClose} className="text-white/80 hover:text-white">
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap ${
              m.role === "user"
                ? "text-white"
                : "text-stone-800"
            } ${m.role === "user" ? "" : "bg-stone-100"
            }`}
            style={m.role === "user" ? { background: "#3E6B4A" } : {}}>
              {m.content}
              {streaming && i === messages.length - 1 && m.role === "assistant" && (
                <span className="inline-block w-1.5 h-3.5 bg-stone-400 rounded-sm ml-0.5 animate-pulse" />
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="p-3 border-t border-stone-100">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Ask about the Rivera family…"
            className="flex-1 text-sm rounded-lg px-3 py-2 focus:outline-none"
            style={{ border: "1px solid rgba(201,169,110,0.3)", background: "#FAF5ED", color: "#1E1208" }}
            disabled={streaming}
          />
          <button
            onClick={send}
            disabled={streaming || !input.trim()}
            className="px-3 py-2 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
            style={{ background: "#3E6B4A", color: "#FAF5ED", fontFamily: "'Jost', sans-serif" }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Demo Page ──────────────────────────────────────────────────────────

type Tab = "meals" | "grocery" | "supplements";

export default function DemoPage() {
  const [activeTab, setActiveTab] = useState<Tab>("meals");
  const [selectedMemberId, setSelectedMemberId] = useState(DEMO_FAMILY.members[0].id);
  const [chatOpen, setChatOpen] = useState(false);

  const selectedMember = DEMO_FAMILY.members.find((m) => m.id === selectedMemberId)!;

  return (
    <div className="min-h-screen" style={{ background: "#FAF5ED" }}>
      {/* Demo Banner */}
      <div className="text-center py-2 text-sm font-medium" style={{ background: "#2E4A35", color: "#FAF5ED", fontFamily: "'Jost', sans-serif", fontSize: "12px", letterSpacing: "0.05em" }}>
        ✦ Investor Demo Mode — Pre-loaded with the Rivera Family · Live AI chat is active
      </div>

      {/* Nav */}
      <header className="sticky top-0 z-40 border-b" style={{ background: "rgba(250,245,237,0.92)", backdropFilter: "blur(12px)", borderColor: "rgba(201,169,110,0.18)" }}>
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <VitaRootsLogo size={24} />
            <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "18px", fontWeight: 700, color: "#1E1208" }}>
              Vita<span style={{ color: "#3E6B4A" }}>Roots</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-xs text-stone-400 bg-stone-100 px-3 py-1.5 rounded-lg">
              <Shield className="w-3.5 h-3.5" />
              Informational only · Not medical advice
            </div>
            <Link href="/" className="text-sm text-stone-500 hover:text-stone-700">← Home</Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6 flex gap-6">

        {/* ── Left sidebar ── */}
        <aside className="w-64 flex-shrink-0 space-y-4">
          {/* family summary */}
          <div className="bg-white border border-stone-200 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-4 h-4 text-brand-500" />
              <span className="font-bold text-stone-900 text-sm">{DEMO_FAMILY.name}</span>
            </div>
            <div className="space-y-1 text-xs text-stone-500">
              <div className="flex justify-between">
                <span>Weekly budget</span>
                <span className="font-semibold text-stone-700">${DEMO_FAMILY.budget_weekly}</span>
              </div>
              <div className="flex justify-between">
                <span>Members</span>
                <span className="font-semibold text-stone-700">{DEMO_FAMILY.members.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Estimated spend</span>
                <span className="font-semibold text-brand-600">${DEMO_GROCERY_LIST.total_estimated_cost}</span>
              </div>
            </div>
          </div>

          {/* member cards */}
          <div className="space-y-2">
            {DEMO_FAMILY.members.map((m) => (
              <button
                key={m.id}
                onClick={() => setSelectedMemberId(m.id)}
                className={`w-full text-left p-3 rounded-xl border transition-all ${
                  selectedMemberId === m.id
                    ? "border-brand-400 bg-brand-50"
                    : "border-stone-200 bg-white hover:border-brand-200"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-7 h-7 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-sm">
                    {m.name[0]}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-stone-900">{m.name}, {m.age}</p>
                    <p className="text-xs text-stone-400">{m.life_stage} · {m.dietary_style.replace(/_/g, " ")}</p>
                  </div>
                </div>
                <PhilosophyBadge philosophy={m.wellness_philosophy} dosha={m.dosha} />
                <div className="flex flex-wrap gap-1 mt-2">
                  {m.goals.slice(0, 2).map((g) => (
                    <span key={g} className="text-xs bg-stone-100 text-stone-600 px-1.5 py-0.5 rounded-full">{g}</span>
                  ))}
                </div>
              </button>
            ))}
          </div>

          {/* stats */}
          <div className="bg-brand-600 text-white rounded-2xl p-4 space-y-3">
            <p className="text-sm font-bold">This Week</p>
            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="bg-white/10 rounded-xl p-2">
                <p className="text-lg font-bold">21</p>
                <p className="text-xs text-brand-100">Meals Planned</p>
              </div>
              <div className="bg-white/10 rounded-xl p-2">
                <p className="text-lg font-bold">40</p>
                <p className="text-xs text-brand-100">Grocery Items</p>
              </div>
              <div className="bg-white/10 rounded-xl p-2">
                <p className="text-lg font-bold">13</p>
                <p className="text-xs text-brand-100">Supplements</p>
              </div>
              <div className="bg-white/10 rounded-xl p-2">
                <p className="text-lg font-bold">$56</p>
                <p className="text-xs text-brand-100">Under Budget</p>
              </div>
            </div>
          </div>
        </aside>

        {/* ── Main content ── */}
        <main className="flex-1 min-w-0 space-y-5">
          {/* tab bar */}
          <div className="flex gap-2 bg-white border border-stone-200 p-1.5 rounded-xl w-fit">
            {([
              { id: "meals", label: "Meal Plan", icon: Sparkles },
              { id: "grocery", label: "Grocery List", icon: ShoppingCart },
              { id: "supplements", label: "Wellness Guide", icon: Heart },
            ] as { id: Tab; label: string; icon: any }[]).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === id
                    ? "bg-brand-600 text-white shadow-sm"
                    : "text-stone-500 hover:text-stone-700"
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {/* ── Meals tab ── */}
          {activeTab === "meals" && (
            <div className="space-y-4">
              {/* member filter tabs */}
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={() => setSelectedMemberId("")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    selectedMemberId === ""
                      ? "bg-stone-800 text-white border-stone-800"
                      : "bg-white text-stone-500 border-stone-200 hover:border-stone-400"
                  }`}
                >
                  All Members
                </button>
                {DEMO_FAMILY.members.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setSelectedMemberId(m.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                      selectedMemberId === m.id
                        ? "bg-brand-600 text-white border-brand-600"
                        : "bg-white text-stone-500 border-stone-200 hover:border-brand-300"
                    }`}
                  >
                    {m.name}
                  </button>
                ))}
              </div>

              <p className="text-xs text-stone-400 italic">
                {DEMO_MEAL_PLAN.notes}
              </p>

              {/* day columns */}
              <div className="grid grid-cols-3 gap-4">
                {DEMO_MEAL_PLAN.days.map((day) => (
                  <div key={day.day} className="space-y-2">
                    <div className="bg-brand-600 text-white text-center py-1.5 rounded-lg text-sm font-bold">
                      {day.day}
                    </div>
                    <div className="space-y-2">
                      <div>
                        <p className="text-xs text-stone-400 font-semibold mb-1">BREAKFAST</p>
                        <MealCard meal={day.breakfast} members={DEMO_FAMILY.members} />
                      </div>
                      <div>
                        <p className="text-xs text-stone-400 font-semibold mb-1">LUNCH</p>
                        <MealCard meal={day.lunch} members={DEMO_FAMILY.members} />
                      </div>
                      <div>
                        <p className="text-xs text-stone-400 font-semibold mb-1">DINNER</p>
                        <MealCard meal={day.dinner} members={DEMO_FAMILY.members} />
                      </div>
                      {day.snacks?.length > 0 && (
                        <div>
                          <p className="text-xs text-stone-400 font-semibold mb-1">SNACKS</p>
                          {day.snacks.map((snack) => (
                            <MealCard key={snack.id} meal={snack} members={DEMO_FAMILY.members} />
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <p className="text-center text-xs text-stone-400 py-4">
                Full 7-day plan generated by Claude · Showing Mon–Wed for demo
              </p>
            </div>
          )}

          {/* ── Grocery tab ── */}
          {activeTab === "grocery" && <GrocerySection />}

          {/* ── Supplements tab ── */}
          {activeTab === "supplements" && (
            <div className="space-y-4">
              <div className="flex gap-2 flex-wrap">
                {DEMO_FAMILY.members.map((m) => (
                  <MemberTab
                    key={m.id}
                    member={m}
                    selected={selectedMemberId === m.id}
                    onClick={() => setSelectedMemberId(m.id)}
                  />
                ))}
              </div>
              <SupplementSection memberId={selectedMemberId} />
            </div>
          )}
        </main>
      </div>

      {/* Floating chat button */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-xl transition-colors flex items-center justify-center z-40"
          style={{ background: "#1E1208", color: "#FAF5ED" }}
        >
          <MessageCircle className="w-6 h-6" />
        </button>
      )}

      {chatOpen && <DemoChat onClose={() => setChatOpen(false)} />}
    </div>
  );
}
