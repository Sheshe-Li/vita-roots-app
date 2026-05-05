"use client";

import { User, Edit2 } from "lucide-react";

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

const PHILOSOPHY_CONFIG: Record<
  string,
  { label: string; color: string }
> = {
  ayurvedic: { label: "Ayurvedic", color: "badge-purple" },
  tcm: { label: "TCM", color: "badge-blue" },
  western_integrative: { label: "Western", color: "badge-green" },
  blend: { label: "Blend", color: "badge-yellow" },
  no_preference: { label: "Open", color: "badge bg-stone-100 text-stone-600" },
};

const LIFE_STAGE_EMOJI: Record<string, string> = {
  infant: "👶",
  child: "🧒",
  teen: "🧑",
  adult: "🙂",
  elderly: "👴",
  pregnant: "🤰",
  postpartum: "🤱",
};

const AVATAR_COLORS = [
  "bg-brand-100 text-brand-700",
  "bg-warm-100 text-warm-700",
  "bg-purple-100 text-purple-700",
  "bg-blue-100 text-blue-700",
  "bg-pink-100 text-pink-700",
  "bg-orange-100 text-orange-700",
];

interface Props {
  member: FamilyMember;
  isSelected: boolean;
  onSelect: () => void;
  colorIndex?: number;
}

export default function FamilyMemberCard({
  member,
  isSelected,
  onSelect,
  colorIndex = 0,
}: Props) {
  const avatarColor = AVATAR_COLORS[colorIndex % AVATAR_COLORS.length];
  const philosophy = PHILOSOPHY_CONFIG[member.wellness_philosophy] ||
    PHILOSOPHY_CONFIG.no_preference;
  const emoji = LIFE_STAGE_EMOJI[member.life_stage] || "🙂";

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-3 rounded-xl border-2 transition-all duration-200 group ${
        isSelected
          ? "border-brand-400 bg-brand-50 shadow-sm"
          : "border-transparent bg-white hover:border-stone-200 hover:shadow-sm"
      }`}
    >
      <div className="flex items-center gap-3">
        {/* Avatar */}
        <div
          className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0 font-semibold ${avatarColor}`}
        >
          {member.name.charAt(0).toUpperCase()}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-semibold text-stone-900 truncate">
              {member.name}
            </span>
            <span className="text-base" title={member.life_stage}>
              {emoji}
            </span>
          </div>
          <p className="text-xs text-stone-400 truncate">
            {member.age}y · {member.dietary_style.replace(/_/g, " ")}
          </p>
        </div>

        {/* Edit button (shows on hover) */}
        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
          <Edit2 className="w-3.5 h-3.5 text-stone-400" />
        </div>
      </div>

      {/* Philosophy tag */}
      <div className="mt-2 flex items-center gap-1.5 flex-wrap">
        <span className={`${philosophy.color} text-xs py-0.5 px-2 rounded-full font-medium`}>
          {philosophy.label}
        </span>
        {member.dosha && member.dosha !== "unknown" && (
          <span className="badge bg-violet-100 text-violet-700 text-xs py-0.5 px-2 rounded-full">
            {member.dosha.charAt(0).toUpperCase() + member.dosha.slice(1).replace(/_/g, "-")}
          </span>
        )}
      </div>

      {/* Goals (collapsed, show 2 max) */}
      {member.goals.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {member.goals.slice(0, 2).map((goal) => (
            <span
              key={goal}
              className="text-xs bg-stone-100 text-stone-500 px-2 py-0.5 rounded-full"
            >
              {goal}
            </span>
          ))}
          {member.goals.length > 2 && (
            <span className="text-xs text-stone-400">+{member.goals.length - 2}</span>
          )}
        </div>
      )}
    </button>
  );
}
