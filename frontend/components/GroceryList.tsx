"use client";

import { useState } from "react";
import {
  ShoppingCart,
  CheckSquare,
  Square,
  Leaf,
  MapPin,
  DollarSign,
  TrendingUp,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

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

interface GroceryListData {
  id: string;
  items: GroceryItem[];
  total_estimated_cost: number;
  budget_weekly: number;
}

interface Props {
  groceryList: GroceryListData | null;
  isLoading: boolean;
  budget: number;
  onToggleItem: (itemId: string, checked: boolean) => void;
}

const CATEGORY_ORDER = [
  "produce",
  "protein",
  "dairy",
  "grains",
  "pantry",
  "frozen",
  "beverages",
  "other",
];

const CATEGORY_ICONS: Record<string, string> = {
  produce: "🥦",
  protein: "🥩",
  dairy: "🧀",
  grains: "🌾",
  pantry: "🫙",
  frozen: "❄️",
  beverages: "🥤",
  other: "🛒",
};

const QUALITY_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  organic: {
    label: "Organic",
    icon: <Leaf className="w-3 h-3" />,
    color: "text-brand-600 bg-brand-50",
  },
  local: {
    label: "Local",
    icon: <MapPin className="w-3 h-3" />,
    color: "text-blue-600 bg-blue-50",
  },
  conventional: {
    label: "Conventional",
    icon: null,
    color: "text-stone-500 bg-stone-100",
  },
};

function CategorySection({
  category,
  items,
  onToggle,
}: {
  category: string;
  items: GroceryItem[];
  onToggle: (id: string, checked: boolean) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const checkedCount = items.filter((i) => i.checked).length;
  const emoji = CATEGORY_ICONS[category] || "🛒";
  const label = category.charAt(0).toUpperCase() + category.slice(1);

  return (
    <div className="mb-4">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between py-2 group"
      >
        <div className="flex items-center gap-2">
          <span className="text-base">{emoji}</span>
          <span className="text-sm font-semibold text-stone-700">{label}</span>
          <span className="text-xs text-stone-400">
            {checkedCount}/{items.length}
          </span>
        </div>
        {collapsed ? (
          <ChevronRight className="w-4 h-4 text-stone-400 group-hover:text-stone-600 transition-colors" />
        ) : (
          <ChevronDown className="w-4 h-4 text-stone-400 group-hover:text-stone-600 transition-colors" />
        )}
      </button>

      {!collapsed && (
        <div className="space-y-1.5">
          {items.map((item) => (
            <GroceryItemRow key={item.id} item={item} onToggle={onToggle} />
          ))}
        </div>
      )}
    </div>
  );
}

function GroceryItemRow({
  item,
  onToggle,
}: {
  item: GroceryItem;
  onToggle: (id: string, checked: boolean) => void;
}) {
  const qualityCfg = item.quality_flag
    ? QUALITY_CONFIG[item.quality_flag]
    : null;

  return (
    <div
      className={`flex items-start gap-2.5 p-2.5 rounded-lg transition-all duration-200 cursor-pointer group ${
        item.checked
          ? "bg-stone-50 opacity-60"
          : "bg-white hover:bg-brand-50 border border-transparent hover:border-brand-100"
      }`}
      onClick={() => onToggle(item.id, !item.checked)}
    >
      {/* Checkbox */}
      <div className="mt-0.5 flex-shrink-0">
        {item.checked ? (
          <CheckSquare className="w-4 h-4 text-brand-500" />
        ) : (
          <Square className="w-4 h-4 text-stone-300 group-hover:text-brand-400 transition-colors" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span
            className={`text-sm font-medium ${
              item.checked ? "line-through text-stone-400" : "text-stone-800"
            }`}
          >
            {item.name}
          </span>
          {qualityCfg && (
            <span
              className={`flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded-full font-medium ${qualityCfg.color}`}
            >
              {qualityCfg.icon}
              {qualityCfg.label}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-stone-400">
            {item.quantity} {item.unit}
          </span>
          {item.member_tags?.length > 0 && (
            <span className="text-xs text-stone-400">
              · {item.member_tags.slice(0, 2).join(", ")}
            </span>
          )}
        </div>
        {item.money_saving_tip && !item.checked && (
          <p className="text-xs text-brand-600 mt-1 italic">
            💡 {item.money_saving_tip}
          </p>
        )}
      </div>

      {/* Cost */}
      <span className="text-xs font-medium text-stone-500 flex-shrink-0 mt-0.5">
        ${item.estimated_cost.toFixed(2)}
      </span>
    </div>
  );
}

export default function GroceryList({
  groceryList,
  isLoading,
  budget,
  onToggleItem,
}: Props) {
  if (isLoading) {
    return (
      <div className="card p-6 text-center">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-stone-200 rounded w-3/4 mx-auto" />
          <div className="h-3 bg-stone-100 rounded w-1/2 mx-auto" />
          <div className="h-3 bg-stone-100 rounded w-2/3 mx-auto" />
        </div>
        <p className="text-xs text-stone-400 mt-4">Generating grocery list...</p>
      </div>
    );
  }

  if (!groceryList || groceryList.items.length === 0) {
    return (
      <div className="card p-6 text-center">
        <ShoppingCart className="w-8 h-8 text-stone-300 mx-auto mb-3" />
        <p className="text-sm font-medium text-stone-500 mb-1">No grocery list yet</p>
        <p className="text-xs text-stone-400">
          Generate a meal plan first, then click "Generate" to build your grocery list.
        </p>
      </div>
    );
  }

  // Group by category
  const grouped: Record<string, GroceryItem[]> = {};
  for (const item of groceryList.items) {
    const cat = item.category || "other";
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(item);
  }

  const sortedCategories = CATEGORY_ORDER.filter((c) => grouped[c]).concat(
    Object.keys(grouped).filter((c) => !CATEGORY_ORDER.includes(c))
  );

  const totalCheckedCost = groceryList.items
    .filter((i) => !i.checked)
    .reduce((sum, i) => sum + i.estimated_cost, 0);

  const effectiveBudget = budget || groceryList.budget_weekly || 1;
  const budgetPercent = Math.min(
    100,
    (groceryList.total_estimated_cost / effectiveBudget) * 100
  );
  const isOverBudget = groceryList.total_estimated_cost > effectiveBudget;

  return (
    <div className="card overflow-hidden">
      {/* Budget progress */}
      <div className="p-4 bg-gradient-to-r from-stone-50 to-white border-b border-stone-100">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <DollarSign className="w-4 h-4 text-stone-500" />
            <span className="text-sm font-semibold text-stone-700">
              Weekly Budget
            </span>
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp
              className={`w-3.5 h-3.5 ${
                isOverBudget ? "text-red-500" : "text-brand-500"
              }`}
            />
            <span
              className={`text-sm font-bold ${
                isOverBudget ? "text-red-600" : "text-stone-800"
              }`}
            >
              ${groceryList.total_estimated_cost.toFixed(0)} /{" "}
              ${effectiveBudget.toFixed(0)}
            </span>
          </div>
        </div>

        <div className="h-2 bg-stone-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isOverBudget ? "bg-red-400" : "bg-brand-500"
            }`}
            style={{ width: `${budgetPercent}%` }}
          />
        </div>

        {isOverBudget && (
          <p className="text-xs text-red-500 mt-1.5">
            ${(groceryList.total_estimated_cost - effectiveBudget).toFixed(2)} over budget
          </p>
        )}

        <div className="flex items-center justify-between mt-2 text-xs text-stone-400">
          <span>
            {groceryList.items.filter((i) => i.checked).length} of{" "}
            {groceryList.items.length} items checked
          </span>
          <span>Remaining: ${totalCheckedCost.toFixed(2)}</span>
        </div>
      </div>

      {/* Items */}
      <div className="p-4 overflow-y-auto" style={{ maxHeight: "500px" }}>
        {sortedCategories.map((cat) => (
          <CategorySection
            key={cat}
            category={cat}
            items={grouped[cat]}
            onToggle={onToggleItem}
          />
        ))}
      </div>
    </div>
  );
}
