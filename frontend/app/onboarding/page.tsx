"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronRight, ChevronLeft, Check, Plus, X } from "lucide-react";

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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ───────────────────────────────────────────────────────────────────

interface MemberForm {
  name: string;
  age: string;
  life_stage: string;
  sex: string;
  activity_level: string;
  dietary_style: string;
  wellness_philosophy: string;
  dosha: string;
  goals: string[];
  allergies: string[];
  dislikes: string[];
  loves: string[];
  cuisine_prefs: string[];
  supplements_open: boolean;
  current_supplements: string[];
  health_conditions: string[];
}

interface FamilyForm {
  name: string;
  member_count: number;
  budget_weekly: string;
  quality_preference: string;
  plan_frequency: string;
  members: MemberForm[];
  disclaimer_accepted: boolean;
}

const defaultMember = (): MemberForm => ({
  name: "",
  age: "",
  life_stage: "adult",
  sex: "prefer_not_to_say",
  activity_level: "moderately_active",
  dietary_style: "omnivore",
  wellness_philosophy: "no_preference",
  dosha: "unknown",
  goals: [],
  allergies: [],
  dislikes: [],
  loves: [],
  cuisine_prefs: [],
  supplements_open: true,
  current_supplements: [],
  health_conditions: [],
});

// ─── Tag Input Component ──────────────────────────────────────────────────────

function TagInput({
  label,
  values,
  onChange,
  placeholder,
}: {
  label: string;
  values: string[];
  onChange: (vals: string[]) => void;
  placeholder?: string;
}) {
  const [input, setInput] = useState("");

  const add = () => {
    const trimmed = input.trim();
    if (trimmed && !values.includes(trimmed)) {
      onChange([...values, trimmed]);
    }
    setInput("");
  };

  return (
    <div>
      <label className="label">{label}</label>
      <div className="flex gap-2 mb-2">
        <input
          className="input-field flex-1"
          value={input}
          placeholder={placeholder || "Type and press Add"}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
        />
        <button type="button" onClick={add} className="btn-secondary px-4 py-2 text-sm">
          Add
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {values.map((v) => (
          <span
            key={v}
            className="badge-green flex items-center gap-1.5 py-1 px-3"
          >
            {v}
            <button
              type="button"
              onClick={() => onChange(values.filter((x) => x !== v))}
              className="hover:text-brand-900 transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}

// ─── Step Components ──────────────────────────────────────────────────────────

function Step1({
  form,
  setForm,
}: {
  form: FamilyForm;
  setForm: (f: FamilyForm) => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-stone-900 mb-2">
          Tell us about your family
        </h2>
        <p className="text-stone-500">
          We'll use this to create a plan that works for everyone.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        <div>
          <label className="label">Family Name</label>
          <input
            className="input-field"
            placeholder="e.g. The Johnson Family"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>

        <div>
          <label className="label">Number of Family Members</label>
          <select
            className="input-field"
            value={form.member_count}
            onChange={(e) =>
              setForm({ ...form, member_count: parseInt(e.target.value) })
            }
          >
            {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
              <option key={n} value={n}>
                {n} {n === 1 ? "member" : "members"}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Weekly Grocery Budget (USD)</label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 font-medium">
              $
            </span>
            <input
              className="input-field pl-8"
              type="number"
              placeholder="200"
              min="20"
              value={form.budget_weekly}
              onChange={(e) => setForm({ ...form, budget_weekly: e.target.value })}
            />
          </div>
        </div>

        <div>
          <label className="label">Food Quality Preference</label>
          <select
            className="input-field"
            value={form.quality_preference}
            onChange={(e) => setForm({ ...form, quality_preference: e.target.value })}
          >
            <option value="whole_foods">Whole Foods Focus</option>
            <option value="organic">Mostly Organic</option>
            <option value="local">Local & Seasonal</option>
            <option value="conventional">Conventional (Budget-conscious)</option>
            <option value="minimally_processed">Minimally Processed</option>
            <option value="budget_friendly">Budget-Friendly</option>
          </select>
        </div>

        <div>
          <label className="label">Plan Frequency</label>
          <select
            className="input-field"
            value={form.plan_frequency}
            onChange={(e) => setForm({ ...form, plan_frequency: e.target.value })}
          >
            <option value="weekly">Weekly</option>
            <option value="biweekly">Bi-weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>
    </div>
  );
}

function MemberStep({
  member,
  index,
  onChange,
}: {
  member: MemberForm;
  index: number;
  onChange: (m: MemberForm) => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-stone-900 mb-2">
          Member {index + 1} Profile
        </h2>
        <p className="text-stone-500">
          The more detail you share, the more personalized the plan.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        <div>
          <label className="label">Name</label>
          <input
            className="input-field"
            placeholder="First name"
            value={member.name}
            onChange={(e) => onChange({ ...member, name: e.target.value })}
          />
        </div>

        <div>
          <label className="label">Age</label>
          <input
            className="input-field"
            type="number"
            placeholder="35"
            min="0"
            max="120"
            value={member.age}
            onChange={(e) => onChange({ ...member, age: e.target.value })}
          />
        </div>

        <div>
          <label className="label">Life Stage</label>
          <select
            className="input-field"
            value={member.life_stage}
            onChange={(e) => onChange({ ...member, life_stage: e.target.value })}
          >
            <option value="infant">Infant (0–1)</option>
            <option value="child">Child (2–11)</option>
            <option value="teen">Teen (12–17)</option>
            <option value="adult">Adult (18–64)</option>
            <option value="elderly">Elderly (65+)</option>
            <option value="pregnant">Pregnant</option>
            <option value="postpartum">Postpartum</option>
          </select>
        </div>

        <div>
          <label className="label">Sex</label>
          <select
            className="input-field"
            value={member.sex}
            onChange={(e) => onChange({ ...member, sex: e.target.value })}
          >
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
            <option value="prefer_not_to_say">Prefer not to say</option>
          </select>
        </div>

        <div>
          <label className="label">Activity Level</label>
          <select
            className="input-field"
            value={member.activity_level}
            onChange={(e) => onChange({ ...member, activity_level: e.target.value })}
          >
            <option value="sedentary">Sedentary (desk job, little exercise)</option>
            <option value="lightly_active">Lightly Active (1–3 days/week)</option>
            <option value="moderately_active">Moderately Active (3–5 days/week)</option>
            <option value="very_active">Very Active (6–7 days/week)</option>
            <option value="extra_active">Extra Active (athlete / physical job)</option>
          </select>
        </div>

        <div>
          <label className="label">Dietary Style</label>
          <select
            className="input-field"
            value={member.dietary_style}
            onChange={(e) => onChange({ ...member, dietary_style: e.target.value })}
          >
            <option value="omnivore">Omnivore</option>
            <option value="vegetarian">Vegetarian</option>
            <option value="vegan">Vegan</option>
            <option value="pescatarian">Pescatarian</option>
            <option value="flexitarian">Flexitarian</option>
            <option value="keto">Keto</option>
            <option value="paleo">Paleo</option>
            <option value="gluten_free">Gluten-Free</option>
            <option value="dairy_free">Dairy-Free</option>
            <option value="halal">Halal</option>
            <option value="kosher">Kosher</option>
            <option value="whole_food_plant_based">Whole Food Plant-Based</option>
          </select>
        </div>

        <div>
          <label className="label">Wellness Philosophy</label>
          <select
            className="input-field"
            value={member.wellness_philosophy}
            onChange={(e) =>
              onChange({ ...member, wellness_philosophy: e.target.value })
            }
          >
            <option value="no_preference">No Preference</option>
            <option value="western_integrative">Western Integrative</option>
            <option value="ayurvedic">Ayurvedic</option>
            <option value="tcm">Traditional Chinese Medicine (TCM)</option>
            <option value="blend">Blend of multiple</option>
          </select>
        </div>

        {member.wellness_philosophy === "ayurvedic" && (
          <div>
            <label className="label">Dosha Type</label>
            <select
              className="input-field"
              value={member.dosha}
              onChange={(e) => onChange({ ...member, dosha: e.target.value })}
            >
              <option value="unknown">Don't know yet</option>
              <option value="vata">Vata</option>
              <option value="pitta">Pitta</option>
              <option value="kapha">Kapha</option>
              <option value="vata_pitta">Vata-Pitta</option>
              <option value="pitta_kapha">Pitta-Kapha</option>
              <option value="vata_kapha">Vata-Kapha</option>
              <option value="tridoshic">Tridoshic</option>
            </select>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-5 pt-2">
        <TagInput
          label="Health Goals"
          values={member.goals}
          onChange={(v) => onChange({ ...member, goals: v })}
          placeholder="e.g. lose weight, build muscle, reduce stress"
        />
        <TagInput
          label="Food Allergies & Intolerances"
          values={member.allergies}
          onChange={(v) => onChange({ ...member, allergies: v })}
          placeholder="e.g. peanuts, dairy, gluten"
        />
        <TagInput
          label="Foods They Dislike"
          values={member.dislikes}
          onChange={(v) => onChange({ ...member, dislikes: v })}
          placeholder="e.g. mushrooms, fish, spicy foods"
        />
        <TagInput
          label="Foods They Love"
          values={member.loves}
          onChange={(v) => onChange({ ...member, loves: v })}
          placeholder="e.g. salmon, avocado, dark chocolate"
        />
        <TagInput
          label="Cuisine Preferences"
          values={member.cuisine_prefs}
          onChange={(v) => onChange({ ...member, cuisine_prefs: v })}
          placeholder="e.g. Mediterranean, Japanese, Mexican"
        />
        <TagInput
          label="Health Conditions (optional)"
          values={member.health_conditions}
          onChange={(v) => onChange({ ...member, health_conditions: v })}
          placeholder="e.g. Type 2 diabetes, IBS, hypothyroid"
        />
      </div>

      <div className="flex items-center gap-3 p-4 bg-stone-50 rounded-xl border border-stone-200">
        <input
          type="checkbox"
          id={`supplements-${index}`}
          checked={member.supplements_open}
          onChange={(e) => onChange({ ...member, supplements_open: e.target.checked })}
          className="w-4 h-4 text-brand-600 rounded focus:ring-brand-500"
        />
        <label htmlFor={`supplements-${index}`} className="text-sm text-stone-700">
          Open to supplement recommendations for {member.name || "this member"}
        </label>
      </div>

      {member.supplements_open && (
        <TagInput
          label="Current Supplements"
          values={member.current_supplements}
          onChange={(v) => onChange({ ...member, current_supplements: v })}
          placeholder="e.g. Vitamin D, Magnesium, Fish Oil"
        />
      )}
    </div>
  );
}

function DisclaimerStep({
  accepted,
  onAccept,
}: {
  accepted: boolean;
  onAccept: (v: boolean) => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-stone-900 mb-2">
          Almost There!
        </h2>
        <p className="text-stone-500">
          Please review our wellness guidance disclaimer before we create your plan.
        </p>
      </div>

      <div className="p-6 bg-amber-50 border border-amber-200 rounded-2xl space-y-4 text-sm text-stone-700 leading-relaxed">
        <h3 className="font-semibold text-stone-900 text-base">
          Wellness Guidance Disclaimer
        </h3>
        <p>
          VitaRoots provides <strong>informational wellness guidance only</strong>.
          Our AI-generated meal plans, grocery lists, and supplement suggestions are not a
          substitute for professional medical advice, diagnosis, or treatment.
        </p>
        <p>
          Always seek the advice of your physician, registered dietitian, or other qualified
          health provider with any questions you may have regarding a medical condition,
          dietary change, or supplement regimen.
        </p>
        <p>
          Never disregard professional medical advice or delay seeking it because of
          something you have read in this application.
        </p>
        <p>
          If you think you may have a medical emergency, call your doctor or emergency
          services immediately.
        </p>
        <p className="font-medium">
          Supplement recommendations are general suggestions based on publicly available
          wellness literature and your stated preferences. Individual responses to
          supplements vary. Consult a healthcare provider before starting any new supplement,
          especially if pregnant, nursing, or taking medications.
        </p>
      </div>

      <div className="flex items-start gap-3 p-4 bg-white rounded-xl border-2 border-stone-200 hover:border-brand-400 transition-colors cursor-pointer"
        onClick={() => onAccept(!accepted)}
      >
        <div className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors ${accepted ? "bg-brand-600" : "border-2 border-stone-300"}`}>
          {accepted && <Check className="w-3 h-3 text-white" />}
        </div>
        <p className="text-sm text-stone-700">
          I understand that this app provides informational wellness guidance only and is not
          medical advice. I agree to consult a licensed healthcare provider before making
          any significant health, dietary, or supplement changes.
        </p>
      </div>
    </div>
  );
}

// ─── Main Onboarding Page ────────────────────────────────────────────────────

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState<FamilyForm>({
    name: "",
    member_count: 2,
    budget_weekly: "",
    quality_preference: "whole_foods",
    plan_frequency: "weekly",
    members: [defaultMember(), defaultMember()],
    disclaimer_accepted: false,
  });

  // Sync member array when count changes
  const updateMemberCount = (newForm: FamilyForm) => {
    const count = newForm.member_count;
    const current = newForm.members;
    if (count > current.length) {
      return {
        ...newForm,
        members: [
          ...current,
          ...Array(count - current.length).fill(null).map(() => defaultMember()),
        ],
      };
    }
    return { ...newForm, members: current.slice(0, count) };
  };

  const handleFormChange = (f: FamilyForm) => {
    setForm(updateMemberCount(f));
  };

  const totalSteps = 2 + form.member_count; // Step1 + N members + disclaimer
  const memberStepStart = 1;
  const disclaimerStep = totalSteps - 1;

  const canAdvance = () => {
    if (step === 0) return form.name.trim() && form.budget_weekly;
    if (step >= memberStepStart && step < disclaimerStep) {
      const m = form.members[step - memberStepStart];
      return m?.name?.trim() && m?.age;
    }
    if (step === disclaimerStep) return form.disclaimer_accepted;
    return true;
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError("");
    try {
      const payload = {
        name: form.name,
        budget_weekly: parseFloat(form.budget_weekly),
        quality_preference: form.quality_preference,
        plan_frequency: form.plan_frequency,
        members: form.members.map((m) => ({
          ...m,
          age: parseInt(m.age),
        })),
      };

      const res = await fetch(`${API_URL}/api/families`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to create family profile.");
      }

      const data = await res.json();
      const familyId = data?.data?.id;
      router.push(`/dashboard?family_id=${familyId}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen" style={{ background: "#FAF5ED" }}>
      {/* Header */}
      <div className="border-b" style={{ background: "rgba(250,245,237,0.9)", backdropFilter: "blur(8px)", borderColor: "rgba(201,169,110,0.18)" }}>
        <div className="max-w-2xl mx-auto px-6 py-4 flex items-center gap-2.5">
          <VitaRootsLogo size={24} />
          <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "18px", fontWeight: 700, color: "#1E1208" }}>
            Vita<span style={{ color: "#3E6B4A" }}>Roots</span>
          </span>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-10">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-sm text-stone-500 mb-2">
            <span>Step {step + 1} of {totalSteps}</span>
            <span>{Math.round(((step + 1) / totalSteps) * 100)}% complete</span>
          </div>
          <div className="h-2 bg-stone-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full transition-all duration-500"
              style={{ width: `${((step + 1) / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Step content */}
        <div className="card p-8 mb-6 animate-fade-in">
          {step === 0 && <Step1 form={form} setForm={handleFormChange} />}
          {step >= memberStepStart && step < disclaimerStep && (
            <MemberStep
              member={form.members[step - memberStepStart]}
              index={step - memberStepStart}
              onChange={(m) => {
                const updated = [...form.members];
                updated[step - memberStepStart] = m;
                setForm({ ...form, members: updated });
              }}
            />
          )}
          {step === disclaimerStep && (
            <DisclaimerStep
              accepted={form.disclaimer_accepted}
              onAccept={(v) => setForm({ ...form, disclaimer_accepted: v })}
            />
          )}
        </div>

        {error && (
          <div className="p-4 mb-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setStep(Math.max(0, step - 1))}
            disabled={step === 0}
            className="btn-ghost disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back
          </button>

          {step < totalSteps - 1 ? (
            <button
              type="button"
              onClick={() => setStep(step + 1)}
              disabled={!canAdvance()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!canAdvance() || isLoading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  Creating Plan
                  <span className="ml-1 loading-dots" />
                </>
              ) : (
                <>
                  Create My Family Plan
                  <Check className="w-4 h-4 ml-2" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
