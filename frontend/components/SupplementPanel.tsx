"use client";

import { useState, useEffect } from "react";
import {
  ChevronDown,
  ChevronRight,
  Heart,
  AlertTriangle,
  Clock,
  Pill,
  Sparkles,
  Loader2,
  ShieldAlert,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SupplementRecommendation {
  id: string;
  name: string;
  purpose: string;
  dose_range: string;
  timing: string;
  approach: string;
  contraindication_notes?: string;
  form?: string;
  brand_suggestions: string[];
}

interface SupplementGuide {
  id: string;
  member_id: string;
  member_name: string;
  recommendations: SupplementRecommendation[];
  disclaimer: string;
}

interface FamilyMember {
  id: string;
  name: string;
  supplements_open: boolean;
}

interface Props {
  familyId: string;
  members: FamilyMember[];
}

const APPROACH_CONFIG: Record<string, { label: string; color: string }> = {
  ayurvedic: { label: "Ayurvedic", color: "badge-purple" },
  tcm: { label: "TCM", color: "badge-blue" },
  "western integrative": { label: "Western", color: "badge-green" },
  general: { label: "General", color: "badge bg-stone-100 text-stone-600" },
};

function SupplementCard({ rec }: { rec: SupplementRecommendation }) {
  const [expanded, setExpanded] = useState(false);
  const approachKey = rec.approach.toLowerCase();
  const approachCfg =
    APPROACH_CONFIG[approachKey] || APPROACH_CONFIG.general;

  return (
    <div className="card border border-stone-100 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-4 flex items-start justify-between gap-3 group"
      >
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
            <Pill className="w-4 h-4 text-purple-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className="font-semibold text-stone-900 text-sm">
                {rec.name}
              </span>
              {rec.form && (
                <span className="text-xs text-stone-400">({rec.form})</span>
              )}
              <span className={`${approachCfg.color} text-xs py-0.5 px-2 rounded-full`}>
                {approachCfg.label}
              </span>
            </div>
            <p className="text-xs text-stone-500 line-clamp-1">{rec.purpose}</p>
          </div>
        </div>
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-stone-400 flex-shrink-0 mt-1" />
        ) : (
          <ChevronRight className="w-4 h-4 text-stone-400 flex-shrink-0 mt-1" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-0 space-y-3 border-t border-stone-50 animate-slide-up">
          {/* Purpose */}
          <div className="flex gap-2">
            <Heart className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-stone-700">{rec.purpose}</p>
          </div>

          {/* Dose & Timing */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-stone-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-stone-400 mb-1">Dose Range</p>
              <p className="text-sm font-medium text-stone-800">{rec.dose_range}</p>
            </div>
            <div className="bg-stone-50 rounded-lg p-3">
              <div className="flex items-center gap-1 mb-1">
                <Clock className="w-3 h-3 text-stone-400" />
                <p className="text-xs font-semibold text-stone-400">Timing</p>
              </div>
              <p className="text-sm font-medium text-stone-800">{rec.timing}</p>
            </div>
          </div>

          {/* Contraindications */}
          {rec.contraindication_notes && (
            <div className="flex gap-2 p-3 bg-amber-50 rounded-lg border border-amber-100">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-amber-800 leading-relaxed">
                {rec.contraindication_notes}
              </p>
            </div>
          )}

          {/* Brand suggestions */}
          {rec.brand_suggestions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-stone-400 mb-1.5">
                Quality Brands to Consider
              </p>
              <div className="flex flex-wrap gap-1.5">
                {rec.brand_suggestions.map((brand) => (
                  <span
                    key={brand}
                    className="text-xs bg-white border border-stone-200 text-stone-600 px-2 py-1 rounded-lg"
                  >
                    {brand}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MemberAccordion({
  member,
  familyId,
}: {
  member: FamilyMember;
  familyId: string;
}) {
  const [open, setOpen] = useState(false);
  const [guide, setGuide] = useState<SupplementGuide | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const loadGuide = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/supplements/${member.id}`);
      if (res.ok) {
        const data = await res.json();
        setGuide(data.data);
      }
    } catch {
      // No guide yet — that's fine
    } finally {
      setLoading(false);
    }
  };

  const generateGuide = async () => {
    setGenerating(true);
    setError("");
    try {
      const res = await fetch(
        `${API_URL}/api/supplements/generate/${member.id}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ family_id: familyId }),
        }
      );
      if (!res.ok) throw new Error("Failed to generate supplement guide.");
      const data = await res.json();
      setGuide(data.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setGenerating(false);
    }
  };

  const handleToggle = () => {
    setOpen(!open);
    if (!open && !guide) loadGuide();
  };

  if (!member.supplements_open) {
    return (
      <div className="card p-4 opacity-60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-stone-100 rounded-lg flex items-center justify-center">
            <span className="text-sm font-bold text-stone-500">
              {member.name.charAt(0)}
            </span>
          </div>
          <div>
            <p className="text-sm font-semibold text-stone-600">{member.name}</p>
            <p className="text-xs text-stone-400">
              Not opted in for supplement guidance
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-stone-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-purple-100 rounded-xl flex items-center justify-center font-bold text-purple-700">
            {member.name.charAt(0)}
          </div>
          <div>
            <p className="font-semibold text-stone-900 text-sm">{member.name}</p>
            <p className="text-xs text-stone-400">
              {guide
                ? `${guide.recommendations.length} supplement${guide.recommendations.length !== 1 ? "s" : ""} recommended`
                : "Tap to view recommendations"}
            </p>
          </div>
        </div>
        {open ? (
          <ChevronDown className="w-4 h-4 text-stone-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-stone-400" />
        )}
      </button>

      {open && (
        <div className="p-4 pt-0 border-t border-stone-50 space-y-4 animate-slide-up">
          {loading && (
            <div className="flex items-center gap-2 py-4 justify-center">
              <Loader2 className="w-4 h-4 animate-spin text-stone-400" />
              <span className="text-sm text-stone-400">Loading...</span>
            </div>
          )}

          {!loading && !guide && (
            <div className="text-center py-4">
              <p className="text-sm text-stone-500 mb-3">
                No supplement guide for {member.name} yet.
              </p>
              <button
                onClick={generateGuide}
                disabled={generating}
                className="btn-primary text-sm py-2 px-5"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5 mr-2" />
                    Generate Guide
                  </>
                )}
              </button>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg text-sm text-red-600">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {guide && (
            <>
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-stone-400 uppercase tracking-wider">
                  Recommendations
                </p>
                <button
                  onClick={generateGuide}
                  disabled={generating}
                  className="text-xs text-brand-600 hover:text-brand-700 font-medium transition-colors"
                >
                  {generating ? "Regenerating..." : "Regenerate"}
                </button>
              </div>

              <div className="space-y-2">
                {guide.recommendations.map((rec) => (
                  <SupplementCard key={rec.id} rec={rec} />
                ))}
              </div>

              {/* Disclaimer */}
              <div className="flex gap-2 p-3 bg-blue-50 rounded-xl border border-blue-100">
                <ShieldAlert className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-blue-700 leading-relaxed">
                  {guide.disclaimer}
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function SupplementPanel({ familyId, members }: Props) {
  if (!members || members.length === 0) {
    return (
      <div className="card p-6 text-center">
        <Heart className="w-8 h-8 text-stone-300 mx-auto mb-3" />
        <p className="text-sm text-stone-500">
          Add family members to get personalized supplement guidance.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-stone-700">
          Supplement Guidance
        </h3>
        <span className="text-xs text-stone-400">Tap a member to expand</span>
      </div>

      {members.map((member) => (
        <MemberAccordion key={member.id} member={member} familyId={familyId} />
      ))}

      <div className="flex gap-1.5 p-3 bg-amber-50 rounded-xl border border-amber-100">
        <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-amber-700">
          Supplement suggestions are informational only. Always consult a licensed
          healthcare provider before starting any new supplement.
        </p>
      </div>
    </div>
  );
}
